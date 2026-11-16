# make -C infrastructure module-test MODULE=nginx_containers
mock_provider "scaleway" {
  # scaleway_container_domain checks the format of container_id
  mock_resource "scaleway_container" {
    defaults = {
      id = "fr-par/11111111-1111-1111-1111-111111111111"
    }
  }
}

variables {
  environment          = "preprod"
  prefix               = "lvao"
  nginx_registry_image = "rg.fr-par.scw.cloud/ns-qfdmo/nginx-gateway:abc123"
  nginx_cpu_limit      = 500
  nginx_memory_limit   = 512
  nginx_min_scale      = 1
  nginx_max_scale      = 2
  nginx_timeout        = 300
  routes = {
    airflow = {
      hostname = "airflow.preprod.example.fr"
      upstream = "airflow.functions.fnc.fr-par.scw.cloud"
    }
  }
  webapp = {
    upstream     = "https://webapp.functions.fnc.fr-par.scw.cloud"
    release      = "rg.fr-par.scw.cloud/ns-qfdmo/webapp:preprod-abc123"
    base_domain  = "webapp.preprod.example.fr"
    environment  = "staging"
    server_names = ["webapp.preprod.example.fr", "alias.preprod.example.fr"]
    domains      = ["webapp.preprod.example.fr"]
    privacy      = "public"
  }
}

run "without_webapp_the_gateway_serves_only_the_routes" {
  command = plan

  variables {
    webapp            = null
    webapp_auth_token = "0b1c2d3e-4f50-6172-8394-a5b6c7d8e9f0"
  }

  assert {
    condition     = scaleway_container.nginx.secret_environment_variables == null
    error_message = "No key sent without a webapp"
  }
  assert {
    condition     = length([for k in keys(scaleway_container.nginx.environment_variables) : k if startswith(k, "WEBAPP_")]) == 0
    error_message = "No WEBAPP_* variable without a webapp"
  }
  assert {
    condition     = length(scaleway_container_domain.webapp) == 0
    error_message = "No webapp domain without a webapp"
  }
}

run "the_webapp_variables_reach_the_container" {
  command = plan

  assert {
    condition = (
      scaleway_container.nginx.environment_variables["WEBAPP_UPSTREAM"] == "https://webapp.functions.fnc.fr-par.scw.cloud"
      && scaleway_container.nginx.environment_variables["WEBAPP_RELEASE"] == "rg.fr-par.scw.cloud/ns-qfdmo/webapp:preprod-abc123"
      && scaleway_container.nginx.environment_variables["WEBAPP_BASE_DOMAIN"] == "webapp.preprod.example.fr"
      && scaleway_container.nginx.environment_variables["WEBAPP_ENVIRONMENT"] == "staging"
      && scaleway_container.nginx.environment_variables["WEBAPP_SERVER_NAMES"] == "webapp.preprod.example.fr alias.preprod.example.fr"
      && scaleway_container.nginx.environment_variables["ROUTE_AIRFLOW_HOST"] == "airflow.preprod.example.fr"
    )
    error_message = "WEBAPP_* and ROUTE_* variables"
  }
  assert {
    condition     = keys(scaleway_container_domain.webapp) == ["webapp.preprod.example.fr"]
    error_message = "One domain per entry of webapp.domains"
  }
  assert {
    condition     = length(nonsensitive(coalesce(scaleway_container.nginx.secret_environment_variables, {}))) == 0
    error_message = "No key sent without webapp_auth_token"
  }
}

run "the_key_goes_in_a_secret_variable" {
  command = plan

  variables {
    webapp_auth_token = "0b1c2d3e-4f50-6172-8394-a5b6c7d8e9f0"
  }

  assert {
    condition     = nonsensitive(scaleway_container.nginx.secret_environment_variables["WEBAPP_AUTH_TOKEN"]) == "0b1c2d3e-4f50-6172-8394-a5b6c7d8e9f0"
    error_message = "WEBAPP_AUTH_TOKEN is a secret environment variable"
  }
  assert {
    condition     = !contains(keys(scaleway_container.nginx.environment_variables), "WEBAPP_AUTH_TOKEN")
    error_message = "The key never goes in the plain environment"
  }
}

run "a_malformed_key_fails_the_plan" {
  command = plan

  variables {
    webapp_auth_token = "not-a-uuid"
  }

  expect_failures = [var.webapp_auth_token]
}

run "an_uppercase_key_fails_the_plan" {
  command = plan

  variables {
    webapp_auth_token = "0B1C2D3E-4F50-6172-8394-A5B6C7D8E9F0"
  }

  expect_failures = [var.webapp_auth_token]
}

run "a_key_inside_a_longer_value_fails_the_plan" {
  command = plan

  variables {
    webapp_auth_token = "x0b1c2d3e-4f50-6172-8394-a5b6c7d8e9f0y"
  }

  expect_failures = [var.webapp_auth_token]
}

run "a_base_domain_outside_server_names_fails_the_plan" {
  command = plan

  variables {
    webapp = {
      upstream     = "https://webapp.functions.fnc.fr-par.scw.cloud"
      release      = "rg.fr-par.scw.cloud/ns-qfdmo/webapp:preprod-abc123"
      base_domain  = "webapp.preprod.example.fr"
      environment  = "staging"
      server_names = ["alias.preprod.example.fr"]
      domains      = []
      privacy      = "public"
    }
  }

  expect_failures = [var.webapp]
}

run "a_release_without_tag_fails_the_plan" {
  command = plan

  variables {
    webapp = {
      upstream     = "https://webapp.functions.fnc.fr-par.scw.cloud"
      release      = "rg.fr-par.scw.cloud/ns-qfdmo/webapp"
      base_domain  = "webapp.preprod.example.fr"
      environment  = "staging"
      server_names = ["webapp.preprod.example.fr"]
      domains      = ["webapp.preprod.example.fr"]
      privacy      = "public"
    }
  }

  expect_failures = [var.webapp]
}

run "a_webapp_domain_already_routed_fails_the_plan" {
  command = plan

  variables {
    webapp = {
      upstream     = "https://webapp.functions.fnc.fr-par.scw.cloud"
      release      = "rg.fr-par.scw.cloud/ns-qfdmo/webapp:preprod-abc123"
      base_domain  = "webapp.preprod.example.fr"
      environment  = "staging"
      server_names = ["webapp.preprod.example.fr", "airflow.preprod.example.fr"]
      domains      = ["webapp.preprod.example.fr", "airflow.preprod.example.fr"]
      privacy      = "public"
    }
  }

  expect_failures = [scaleway_container_domain.webapp]
}

run "an_http_upstream_fails_the_plan" {
  command = plan

  variables {
    webapp = {
      upstream     = "http://webapp.functions.fnc.fr-par.scw.cloud"
      release      = "rg.fr-par.scw.cloud/ns-qfdmo/webapp:preprod-abc123"
      base_domain  = "webapp.preprod.example.fr"
      environment  = "staging"
      server_names = ["webapp.preprod.example.fr"]
      domains      = ["webapp.preprod.example.fr"]
      privacy      = "public"
    }
  }

  expect_failures = [var.webapp]
}

run "the_gateway_environment_name_fails_the_plan" {
  command = plan

  variables {
    webapp = {
      upstream     = "https://webapp.functions.fnc.fr-par.scw.cloud"
      release      = "rg.fr-par.scw.cloud/ns-qfdmo/webapp:preprod-abc123"
      base_domain  = "webapp.preprod.example.fr"
      environment  = "preprod"
      server_names = ["webapp.preprod.example.fr"]
      domains      = ["webapp.preprod.example.fr"]
      privacy      = "public"
    }
  }

  expect_failures = [var.webapp]
}

run "a_domain_outside_server_names_fails_the_plan" {
  command = plan

  variables {
    webapp = {
      upstream     = "https://webapp.functions.fnc.fr-par.scw.cloud"
      release      = "rg.fr-par.scw.cloud/ns-qfdmo/webapp:preprod-abc123"
      base_domain  = "webapp.preprod.example.fr"
      environment  = "staging"
      server_names = ["webapp.preprod.example.fr"]
      domains      = ["other.preprod.example.fr"]
      privacy      = "public"
    }
  }

  expect_failures = [var.webapp]
}

run "a_private_webapp_without_key_fails_the_plan" {
  command = plan

  variables {
    webapp = {
      upstream     = "https://webapp.functions.fnc.fr-par.scw.cloud"
      release      = "rg.fr-par.scw.cloud/ns-qfdmo/webapp:preprod-abc123"
      base_domain  = "webapp.preprod.example.fr"
      environment  = "staging"
      server_names = ["webapp.preprod.example.fr"]
      domains      = ["webapp.preprod.example.fr"]
      privacy      = "private"
    }
  }

  expect_failures = [scaleway_container.nginx]
}

run "a_private_webapp_with_its_key_plans" {
  command = plan

  variables {
    webapp_auth_token = "0b1c2d3e-4f50-6172-8394-a5b6c7d8e9f0"
    webapp = {
      upstream     = "https://webapp.functions.fnc.fr-par.scw.cloud"
      release      = "rg.fr-par.scw.cloud/ns-qfdmo/webapp:preprod-abc123"
      base_domain  = "webapp.preprod.example.fr"
      environment  = "staging"
      server_names = ["webapp.preprod.example.fr"]
      domains      = ["webapp.preprod.example.fr"]
      privacy      = "private"
    }
  }

  assert {
    condition     = nonsensitive(scaleway_container.nginx.secret_environment_variables["WEBAPP_AUTH_TOKEN"]) == "0b1c2d3e-4f50-6172-8394-a5b6c7d8e9f0"
    error_message = "The key reaches the gateway"
  }
}

run "an_unknown_privacy_fails_the_plan" {
  command = plan

  variables {
    webapp = {
      upstream     = "https://webapp.functions.fnc.fr-par.scw.cloud"
      release      = "rg.fr-par.scw.cloud/ns-qfdmo/webapp:preprod-abc123"
      base_domain  = "webapp.preprod.example.fr"
      environment  = "staging"
      server_names = ["webapp.preprod.example.fr"]
      domains      = ["webapp.preprod.example.fr"]
      privacy      = "Private"
    }
  }

  expect_failures = [var.webapp]
}

run "the_gateway_tells_whether_it_holds_the_key" {
  command = plan

  variables {
    webapp_auth_token = "0b1c2d3e-4f50-6172-8394-a5b6c7d8e9f0"
  }

  assert {
    condition     = output.webapp_auth_token_set == true
    error_message = "webapp_auth_token_set with a key"
  }
}

run "the_gateway_tells_it_has_no_key" {
  command = plan

  assert {
    condition     = output.webapp_auth_token_set == false
    error_message = "webapp_auth_token_set without a key"
  }
}

run "the_key_is_not_set_without_a_webapp" {
  command = plan

  variables {
    webapp            = null
    webapp_auth_token = "0b1c2d3e-4f50-6172-8394-a5b6c7d8e9f0"
  }

  assert {
    condition     = output.webapp_auth_token_set == false
    error_message = "webapp_auth_token_set while the key is not sent"
  }
}

run "without_previews_no_preview_variable" {
  command = plan

  assert {
    condition     = length([for k in keys(scaleway_container.nginx.environment_variables) : k if startswith(k, "WEBAPP_PREVIEW_")]) == 0
    error_message = "No WEBAPP_PREVIEW_* variable without previews"
  }
}

run "the_previews_variables_reach_the_container" {
  command = plan

  variables {
    previews = {
      domain   = "preview.example.fr"
      upstream = "https://nspreview-lvao-pr-{pr}-webapp.functions.fnc.fr-par.scw.cloud"
    }
  }

  assert {
    condition = (
      scaleway_container.nginx.environment_variables["WEBAPP_PREVIEW_DOMAIN"] == "preview.example.fr"
      && scaleway_container.nginx.environment_variables["WEBAPP_PREVIEW_UPSTREAM"] == "https://nspreview-lvao-pr-{pr}-webapp.functions.fnc.fr-par.scw.cloud"
      && scaleway_container.nginx.environment_variables["WEBAPP_UPSTREAM"] == "https://webapp.functions.fnc.fr-par.scw.cloud"
    )
    error_message = "WEBAPP_PREVIEW_* variables next to the WEBAPP_* ones"
  }
}

run "previews_without_webapp_fail_the_plan" {
  command = plan

  variables {
    webapp = null
    previews = {
      domain   = "preview.example.fr"
      upstream = "https://nspreview-lvao-pr-{pr}-webapp.functions.fnc.fr-par.scw.cloud"
    }
  }

  expect_failures = [scaleway_container.nginx]
}

run "a_preview_upstream_without_pr_fails_the_plan" {
  command = plan

  variables {
    previews = {
      domain   = "preview.example.fr"
      upstream = "https://nspreview-lvao-pr-1-webapp.functions.fnc.fr-par.scw.cloud"
    }
  }

  expect_failures = [var.previews]
}

run "an_http_preview_upstream_fails_the_plan" {
  command = plan

  variables {
    previews = {
      domain   = "preview.example.fr"
      upstream = "http://nspreview-lvao-pr-{pr}-webapp.functions.fnc.fr-par.scw.cloud"
    }
  }

  expect_failures = [var.previews]
}

run "a_wildcard_preview_domain_fails_the_plan" {
  command = plan

  variables {
    previews = {
      domain   = "*.preview.example.fr"
      upstream = "https://nspreview-lvao-pr-{pr}-webapp.functions.fnc.fr-par.scw.cloud"
    }
  }

  expect_failures = [var.previews]
}
