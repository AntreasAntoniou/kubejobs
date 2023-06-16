from rich import print


def build_command(
    exp_name, model_name, dataset_name, model_args="", lr=1e-5, seed: int = 42
):
    command_template = (
        f"/opt/conda/envs/main/bin/accelerate-launch --mixed_precision=bf16 --gpu_ids=0 /app/gate/run.py "
        f"exp_name={exp_name} model={model_name} {model_args} dataset={dataset_name} optimizer.lr={lr} "
        f"trainer=image_to_text_zero_shot_classification evaluator=image_to_text_zero_shot_classification "
        f"seed={seed} train_batch_size=128 eval_batch_size=128"
    )
    return command_template


dataset_dict = {
    "winogr": "winoground",
    "flickr30k": "flickr30k",
    "nycc": "newyorkercaptioncontest",
    "pokeset": "pokemonblipcaptions",
}


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
    "clip_vit_base16_224": dict(model_name="clip-zero-shot-classification"),
    "laion_vit_base16_224": dict(
        model_name="timm-zero-shot-classification",
        timm_model_name="vit_base_patch16_clip_224.laion2b",
    ),
    "resnet50_a1_in1k": dict(
        model_name="timm-zero-shot-classification",
        timm_model_name="resnet50.a1_in1k",
    ),
    "sam_vit_base16_224_in1k": dict(
        model_name="timm-zero-shot-classification",
        timm_model_name="vit_base_patch16_224.sam_in1k",
    ),
    "augreg_vit_base16_224_in1k": dict(
        model_name="timm-zero-shot-classification",
        timm_model_name="vit_base_patch16_224.augreg_in1k",
    ),
    "dino_vit_base16_224": dict(
        model_name="timm-zero-shot-classification",
        timm_model_name="vit_base_patch16_224.dino",
    ),
    "wide_resnet50_2_tv_in1k": dict(
        model_name="timm-zero-shot-classification",
        timm_model_name="wide_resnet50_2.tv_in1k",
    ),
    "efficientnetv2_rw_s_ra2_in1k": dict(
        model_name="timm-zero-shot-classification",
        timm_model_name="efficientnetv2_rw_s.ra2_in1k",
    ),
    "deit3_base_patch16_224_fb_in1k": dict(
        model_name="timm-zero-shot-classification",
        timm_model_name="deit3_base_patch16_224.fb_in1k",
    ),
    "resnext50_32x4d_a1_in1k": dict(
        model_name="timm-zero-shot-classification",
        timm_model_name="resnext50_32x4d.a1_in1k",
    ),
    "flexivit_base_1200ep_in1k": dict(
        model_name="timm-zero-shot-classification",
        timm_model_name="flexivit_base.1200ep_in1k",
    ),
}

tali_model_dict = {
    "wits-base16-wit-0": dict(
        model_name="tali-zero-shot-classification",
        model_repo_path="Antreas/wits-godzilla-base16-wit-1337-7",
    ),
    "witp-base16-wit-0": dict(
        model_name="tali-zero-shot-classification",
        model_repo_path="Antreas/witp-godzilla-base16-wit-1337-7",
    ),
    "talis-base16-wita-0": dict(
        model_name="tali-zero-shot-classification",
        model_repo_path="Antreas/talis-godzilla-base16-wita-1337-7",
    ),
    "talip-base16-wita-0": dict(
        model_name="tali-zero-shot-classification",
        model_repo_path="Antreas/talip-godzilla-base16-wita-1337-7",
    ),
    "talip-base16-wiva-0": dict(
        model_name="tali-zero-shot-classification",
        model_repo_path="Antreas/talip-godzilla-base16-wiva-sep-1337",
    ),
    "talis-base16-witav-0": dict(
        model_name="tali-zero-shot-classification",
        model_repo_path="Antreas/talis-godzilla-base16-witav-1337-7",
    ),
    "talip-base16-witav-0": dict(
        model_name="tali-zero-shot-classification",
        model_repo_path="Antreas/talip-godzilla-base16-witav-1337-7",
    ),
}

model_dict = tali_model_dict | model_dict

tali_model_names = [
    "Antreas/wits-godzilla-base16-wit-1337-7",
    "Antreas/witp-godzilla-base16-wit-1337-7",
    "Antreas/talip-godzilla-base16-wita-1337-7",
    "Antreas/talis-godzilla-base16-wita-1337-7",
    "Antreas/talip-godzilla-base16-wiva-sep-1337",
    "Antreas/talip-godzilla-base16-witav-1337-7",
    "Antreas/talis-godzilla-base16-witav-1337-7",
]


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
                    model_name=model_value["model_name"],
                    dataset_name=dataset_value,
                    model_args=model_args,
                    lr=lr_dict[model_key],
                    seed=seed,
                )
                command_dict[exp_name] = command
    return command_dict


def get_commands(prefix):
    # Generate a list of random seeds
    seed_list = [7]

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
