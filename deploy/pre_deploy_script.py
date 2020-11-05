import os
from pathlib import Path

import environ
from django.template import Context, Engine

ROOT_DIR = Path(__file__).resolve(strict=True).parent.parent


def make_prod_requirements_txt():
    req_base_path = ROOT_DIR / "requirements" / "base.txt"
    req_prod_path = ROOT_DIR / "requirements" / "production.txt"
    with open(req_base_path, "r") as f:
        base = f.readlines()
    with open(req_prod_path, "r") as f:
        prod = f.readlines()
    reqs = [line for line in base if not line.startswith("-r")]
    reqs = reqs + [line for line in prod if not line.startswith("-r")]
    with open(ROOT_DIR / "requirements.txt", "w") as f:
        f.writelines(reqs)


def make_app_yaml():
    env = environ.Env()
    env.read_env(str(ROOT_DIR / ".env"))
    with open(ROOT_DIR / "app.yaml.template", "r") as f:
        app_yaml_template = f.read()
    template = Engine().from_string(app_yaml_template)
    context = Context(dict(instance_id=env.str("CLOUD_SQL_INSTANCE_ID")))
    with open(ROOT_DIR / "app.yaml", "w") as f:
        f.write(template.render(context))


def make_dot_env_file():
    print("IN DOT ENV")
    print(os.environ.get("MY_SECRET_ENV", "MY_SECRET_ENV Not Available"))


if __name__ == "__main__":
    make_dot_env_file()
    make_prod_requirements_txt()
    make_app_yaml()
