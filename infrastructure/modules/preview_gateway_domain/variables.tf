variable "environment" {
  description = "pr-<n>, the first label of the preview's host name"
  type        = string

  validation {
    # The server_name of the previews on the gateway
    condition     = can(regex("^pr-[1-9][0-9]*$", var.environment))
    error_message = "environment must be pr-<n>."
  }
}

variable "domain" {
  description = "Domain of the previews served by the gateway (preview_domain of preprod/env.hcl); empty attaches nothing"
  type        = string

  validation {
    condition     = var.domain == "" || can(regex("^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$", var.domain))
    error_message = "domain must be empty or a host name."
  }
}

variable "gateway_namespace" {
  description = "Namespace of the gateway that serves the previews"
  type        = string
}

variable "gateway_container" {
  description = "Container of the gateway that serves the previews"
  type        = string
}
