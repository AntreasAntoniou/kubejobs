from rich import print


def build_image_classification_command(
    exp_name, model, dataset_name, model_args="", seed: int = 42
):
    image_classification_template = (
        f"accelerate launch --mixed_precision=bf16 --gpu_ids=0 gate/run.py "
        f"exp_name=debug-{exp_name} model={model} {model_args} dataset={dataset_name} "
        f"trainer=image_classification evaluator=image_classification "
        f"seed={seed} train_batch_size=128 eval_batch_size=128 train_iters=10 learner.evaluate_every_n_steps=5 learner.limit_val_iters=2"
    )
    return image_classification_template


# evaluate_every_n_steps: 1000
# checkpoint_every_n_steps: 500
# checkpoint_after_validation: true
# train_iters: ${train_iters}
# train_dataloader: null
# limit_train_iters: null
# val_dataloader: null
# limit_val_iters: 1000

dataset_dict = {
    "in1k": "imagenet1k-classification",
    "c100": "cifar100",
    "f101": "food101",
    "stl10": "stl10",
    "svhn": "svhn",
    "p365": "places365",
}

tali_model_names = [
    "Antreas/witp-base16-wit-224-42",
    "Antreas/talip-base16-wit-224-2306",
    "Antreas/talip-base16-wita-224-2306",
    "Antreas/talip-base16-witav-224-2306",
    "Antreas/wits-base16-wit-224-2306",
    "Antreas/talis-base16-wit-224-2306",
    "Antreas/talis-base16-wita-224-2306",
    "Antreas/talis-base16-witav-224-2306",
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

model_dict = {
    "clip_vit_base16_224": dict(model_name="clip-classification"),
    "laion_vit_base16_224": dict(
        model_name="timm-classification",
        timm_model_name="vit_base_patch16_clip_224.laion2b",
    ),
    "witp-base16-wit": dict(
        model_name="tali-classification",
        model_repo_path="Antreas/witp-base16-wit-224-42",
    ),
}

import itertools


def generate_commands(seed_list, dataset_dict, model_dict):
    commands = []
    for dataset_key, dataset_value in dataset_dict.items():
        for model_key, model_value in model_dict.items():
            for seed in seed_list:
                exp_name = f"{dataset_key}-{model_key}-{seed}"
                model_args = ""
                if "timm_model_name" in model_value:
                    model_args = f"model.timm_model_name={model_value['timm_model_name']}"
                elif "model_repo_path" in model_value:
                    model_args = f"model.model_repo_path={model_value['model_repo_path']}"
                command = build_image_classification_command(
                    exp_name,
                    model_value["model_name"],
                    dataset_value,
                    model_args,
                    seed,
                )
                commands.append(command)
    return commands


# Generate a list of random seeds
seed_list = [42]

# Generate all commands
commands = generate_commands(seed_list, dataset_dict, model_dict)

bash_full_command = ";\n".join(commands)

with open("commands.sh", "w") as f:
    f.write("#!/bin/bash\n")
    f.write(bash_full_command)


# print(fish_full_command)

# print(
#     f"Total number of commands: {len(commands)}, each needs 1 GPU hour, so total GPU hours: {len(commands)}"
# )
