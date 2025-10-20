from prefect import flow, serve, task

from data_platform.clone.deployments import (
    deploy_clone_ae_etablissement,
    deploy_clone_ae_unite_legale,
    deploy_clone_ban_adresses,
    deploy_clone_ban_lieux_dits,
)


@task
def task_raise():
    raise Exception("Test raise")


@flow
def flow_raise():
    task_raise()


to_deploy_test_raise = flow_raise.to_deployment(
    name="Test raise",
    description="Test raise",
)

if __name__ == "__main__":
    print("Démarrage des flows de clone")

    # Servir tous les déploiements ensemble
    serve(
        deploy_clone_ae_etablissement,
        deploy_clone_ae_unite_legale,
        deploy_clone_ban_adresses,
        deploy_clone_ban_lieux_dits,
        to_deploy_test_raise,
    )
