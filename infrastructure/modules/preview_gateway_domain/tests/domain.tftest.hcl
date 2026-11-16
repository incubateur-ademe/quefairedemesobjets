# make -C infrastructure module-test MODULE=preview_gateway_domain
mock_provider "scaleway" {
  mock_data "scaleway_container_namespace" {
    defaults = {
      id = "fr-par/22222222-2222-2222-2222-222222222222"
    }
  }
  # scaleway_container_domain checks the format of container_id
  mock_data "scaleway_container" {
    defaults = {
      id = "fr-par/11111111-1111-1111-1111-111111111111"
    }
  }
}

variables {
  environment       = "pr-123"
  domain            = "preview.example.fr"
  gateway_namespace = "lvao-preprod-gateway"
  gateway_container = "lvao-nginx"
}

run "the_preview_domain_goes_on_the_gateway" {
  command = plan

  assert {
    condition = (
      scaleway_container_domain.preview[0].hostname == "pr-123.preview.example.fr"
      && scaleway_container_domain.preview[0].container_id == "fr-par/11111111-1111-1111-1111-111111111111"
    )
    error_message = "pr-<n>.<domain> attached to the gateway container"
  }
  assert {
    condition     = output.url == "https://pr-123.preview.example.fr"
    error_message = "url of the preview"
  }
}

run "without_domain_nothing_is_attached" {
  command = plan

  variables {
    domain = ""
  }

  assert {
    condition     = length(scaleway_container_domain.preview) == 0 && length(data.scaleway_container.gateway) == 0
    error_message = "No domain nor gateway lookup without a domain"
  }
  assert {
    condition     = output.url == ""
    error_message = "No url without a domain"
  }
}

run "an_environment_other_than_a_pr_fails_the_plan" {
  command = plan

  variables {
    environment = "preprod"
  }

  expect_failures = [var.environment]
}

run "a_malformed_domain_fails_the_plan" {
  command = plan

  variables {
    domain = "*.preview.example.fr"
  }

  expect_failures = [var.domain]
}
