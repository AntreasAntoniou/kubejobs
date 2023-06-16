from rich import print


def build_command(
    exp_name, model_name, dataset_name, model_args="", lr=1e-5, seed: int = 42
):
    command_template = (
        f"/opt/conda/envs/main/bin/accelerate-launch --mixed_precision=bf16 --gpu_ids=0 /app/gate/run.py "
        f"exp_name={exp_name} model={model_name} {model_args} dataset={dataset_name} optimizer.lr={lr} "
        f"trainer=visual_relational_reasoning evaluator=visual_relational_reasoning "
        f"seed={seed} train_batch_size=128 eval_batch_size=128"
    )
    return command_template


# accelerate launch --mixed_precision=bf16 gate/run.py exp_name=rr-timm-debug-clevr-0 model=timm-relational-reasoning dataset=clevr trainer=visual_relati
# onal_reasoning evaluator=visual_relational_reasoning seed=2306 train_batch_size=128 eval_batch_size=128 learner.limit_val_iters=1

dataset_dict = {
    "clvr": "clevr",
    "clvrmath": "clevr_math",
}

tali_model_names = [
    "Antreas/witp-godzilla-base16-wit-42",
    "Antreas/talip-godzilla-base16-witav-42",
    "Antreas/wits-godzilla-base16-wit-42",
    "Antreas/talip-godzilla-base16-wita-42",
    "Antreas/talis-godzilla-base16-wita-42",
    "Antreas/talis-godzilla-base16-wit-42",
    "Antreas/talis-godzilla-base16-witav-1337",
]

timm_model_names = [
    "vit_base_patch16_clip_224.laion2b",
    "resnet50.a1_in1k",
    "vit_base_patch16_224.sam_in1k",
    "vit_base_patch16_224.augreg_in1k",
    "vit_base_patch16_224.dino",
    "wide_resnet50_2.tv_in1k",
    "efficientnetv2_rw_s.ra2_in1k",
    "deit3_base_patch16_224.fb_in1k",
    "resnext50_32x4d.a1_in1k",
    "flexivit_base.1200ep_in1k",
]

lr_dict = {
    "resnet50_a1_in1k": 1e-3,
    "wide_resnet50_2_tv_in1k": 1e-3,
    "resnext50_32x4d_a1_in1k": 1e-3,
    "sam_vit_base16_224_in1k": 1e-5,
    "augreg_vit_base16_224_in1k": 1e-5,
    "dino_vit_base16_224": 1e-5,
    "clip_vit_base16_224": 1e-5,
    "laion_vit_base16_224": 1e-5,
    "efficientnetv2_rw_s_ra2_in1k": 1e-5,
    "deit3_base_patch16_224_fb_in1k": 1e-5,
    "flexivit_base_1200ep_in1k": 1e-5,
    "witp-base16-wit-0": 1e-5,
    "talip-base16-wita-0": 1e-5,
    "talip-base16-wiva-0": 1e-5,
    "talip-base16-witav-0": 1e-5,
    "wits-base16-wit-0": 1e-5,
    "talis-base16-wit-0": 1e-5,
    "talis-base16-wita-0": 1e-5,
    "talis-base16-witav-0": 1e-5,
}

model_dict = {
    "clip_vit_base16_224": dict(
        clvr="clip-relational-reasoning-multi-task",
        clvrmath="clip-relational-reasoning",
    ),
    "laion_vit_base16_224": dict(
        clvr="timm-relational-reasoning-multi-task",
        clvrmath="timm-relational-reasoning",
        timm_model_name="vit_base_patch16_clip_224.laion2b",
    ),
    "resnet50_a1_in1k": dict(
        clvr="timm-relational-reasoning-multi-task",
        clvrmath="timm-relational-reasoning",
        timm_model_name="resnet50.a1_in1k",
    ),
    "sam_vit_base16_224_in1k": dict(
        clvr="timm-relational-reasoning-multi-task",
        clvrmath="timm-relational-reasoning",
        timm_model_name="vit_base_patch16_224.sam_in1k",
    ),
    "augreg_vit_base16_224_in1k": dict(
        clvr="timm-relational-reasoning-multi-task",
        clvrmath="timm-relational-reasoning",
        timm_model_name="vit_base_patch16_224.augreg_in1k",
    ),
    "dino_vit_base16_224": dict(
        clvr="timm-relational-reasoning-multi-task",
        clvrmath="timm-relational-reasoning",
        timm_model_name="vit_base_patch16_224.dino",
    ),
    "wide_resnet50_2_tv_in1k": dict(
        clvr="timm-relational-reasoning-multi-task",
        clvrmath="timm-relational-reasoning",
        timm_model_name="wide_resnet50_2.tv_in1k",
    ),
    "efficientnetv2_rw_s_ra2_in1k": dict(
        clvr="timm-relational-reasoning-multi-task",
        clvrmath="timm-relational-reasoning",
        timm_model_name="efficientnetv2_rw_s.ra2_in1k",
    ),
    "deit3_base_patch16_224_fb_in1k": dict(
        clvr="timm-relational-reasoning-multi-task",
        clvrmath="timm-relational-reasoning",
        timm_model_name="deit3_base_patch16_224.fb_in1k",
    ),
    "resnext50_32x4d_a1_in1k": dict(
        clvr="timm-relational-reasoning-multi-task",
        clvrmath="timm-relational-reasoning",
        timm_model_name="resnext50_32x4d.a1_in1k",
    ),
    "flexivit_base_1200ep_in1k": dict(
        clvr="timm-relational-reasoning-multi-task",
        clvrmath="timm-relational-reasoning",
        timm_model_name="flexivit_base.1200ep_in1k",
    ),
    # "wits-gbase16-wit": dict(
    #     clvr="tali-relational-reasoning-multi-task",
    #     clvrmath="tali-relational-reasoning",
    #     model_repo_path="Antreas/wits-godzilla-base16-wit-42",
    # ),
    # "witp-gbase16-wit": dict(
    #     clvr="tali-relational-reasoning-multi-task",
    #     clvrmath="tali-relational-reasoning",
    #     model_repo_path="Antreas/witp-godzilla-base16-wit-42",
    # ),
    # "talis-base16-wit": dict(
    #     clvr="tali-relational-reasoning-multi-task",
    #     clvrmath="tali-relational-reasoning",
    #     model_repo_path="Antreas/talis-godzilla-base16-wit-42",
    # ),
    # "talis-gbase16-wita": dict(
    #     clvr="tali-relational-reasoning-multi-task",
    #     clvrmath="tali-relational-reasoning",
    #     model_repo_path="Antreas/talis-godzilla-base16-wita-42",
    # ),
    # "talip-gbase16-wita": dict(
    #     clvr="tali-relational-reasoning-multi-task",
    #     clvrmath="tali-relational-reasoning",
    #     model_repo_path="Antreas/talip-godzilla-base16-wita-42",
    # ),
    # "talis-base16-witav": dict(
    #     clvr="tali-relational-reasoning-multi-task",
    #     clvrmath="tali-relational-reasoning",
    #     model_repo_path="Antreas/talis-godzilla-base16-witav-1337",
    # ),
    # "talip-gbase16-witav": dict(
    #     clvr="tali-relational-reasoning-multi-task",
    #     clvrmath="tali-relational-reasoning",
    #     model_repo_path="Antreas/talip-godzilla-base16-witav-42",
    # ),
}

tali_model_dict = {
    "wits-base16-wit-0": dict(
        clvr="tali-relational-reasoning-multi-task",
        clvrmath="tali-relational-reasoning",
        model_repo_path="Antreas/wits-godzilla-base16-wit-1337-7",
    ),
    "witp-base16-wit-0": dict(
        clvr="tali-relational-reasoning-multi-task",
        clvrmath="tali-relational-reasoning",
        model_repo_path="Antreas/witp-godzilla-base16-wit-1337-7",
    ),
    "talis-base16-wita-0": dict(
        clvr="tali-relational-reasoning-multi-task",
        clvrmath="tali-relational-reasoning",
        model_repo_path="Antreas/talis-godzilla-base16-wita-1337-7",
    ),
    "talip-base16-wita-0": dict(
        clvr="tali-relational-reasoning-multi-task",
        clvrmath="tali-relational-reasoning",
        model_repo_path="Antreas/talip-godzilla-base16-wita-1337-7",
    ),
    "talip-base16-wiva-0": dict(
        clvr="tali-relational-reasoning-multi-task",
        clvrmath="tali-relational-reasoning",
        model_repo_path="Antreas/talip-godzilla-base16-wiva-sep-1337",
    ),
    "talis-base16-witav-0": dict(
        clvr="tali-relational-reasoning-multi-task",
        clvrmath="tali-relational-reasoning",
        model_repo_path="Antreas/talis-godzilla-base16-witav-1337-7",
    ),
    "talip-base16-witav-0": dict(
        clvr="tali-relational-reasoning-multi-task",
        clvrmath="tali-relational-reasoning",
        model_repo_path="Antreas/talip-godzilla-base16-witav-1337-7",
    ),
}

model_dict: dict[str, dict[str, str]] = tali_model_dict | model_dict


def generate_commands(prefix, seed_list, dataset_dict, model_dict, lr_dict):
    command_dict = {}
    for dataset_key, dataset_value in dataset_dict.items():
        for model_key, model_value in model_dict.items():
            for seed in seed_list:
                exp_name = (
                    f"{prefix}-{dataset_key}-{model_key}-{seed}".replace(
                        "_", "-"
                    )
                )
                model_args = ""
                if "timm_model_name" in model_value:
                    model_args = f"model.timm_model_name={model_value['timm_model_name']}"
                elif "model_repo_path" in model_value:
                    model_args = f"model.model_repo_path={model_value['model_repo_path']}"
                command = build_command(
                    exp_name=exp_name,
                    model_name=model_value[dataset_key],
                    dataset_name=dataset_value,
                    model_args=model_args,
                    lr=lr_dict[model_key],
                    seed=seed,
                )
                command_dict[exp_name] = command
    return command_dict


def get_commands(prefix):
    # Generate a list of random seeds
    seed_list = [7]  # , 2306, 42]  # , 42, 1337, 2306

    # Generate all commands
    command_dict = generate_commands(
        prefix=prefix,
        seed_list=seed_list,
        dataset_dict=dataset_dict,
        model_dict=model_dict,
        lr_dict=lr_dict,
    )

    for name, command in command_dict.items():
        print(f"Command for {name}: {command}")

    print(
        f"Total number of commands: {len(command_dict)}, each needs 1 GPU hour, so total GPU hours: {len(command_dict)}"
    )
    return command_dict


if __name__ == "__main__":
    get_commands(prefix="debug")
