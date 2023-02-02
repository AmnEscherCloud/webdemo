import PIL.Image as Image
import os
import glob
from scripts.img2img import img2img_infer
from scripts.txt2img import txt2img_infer
from scripts.streamlit.superresolution import inference
import shutil
from omegaconf import OmegaConf
import torch 
from ldm.util import instantiate_from_config
from scripts.streamlit.superresolution import initialize_model



def diff_model(
    prompt,
    mode,
    model=None,
    config = None,
    image_path=None,
    strength=0.8,
    dim=(512, 512),
    seed_num=42,
    num_samples=3,
    n_iter=2,
    eta = 0,
    scale =9,
    steps = 50
):

    if mode == "txt2img":
        path, grid_path = txt2img_infer(
            input_prompt=prompt,
            model=model,
            config = config,
            input_plms=True,
            dim=dim,
            seed_num=seed_num,
            n_samples=num_samples,
            n_iter=n_iter,
        )

        images = glob.glob(grid_path + "/*.png")
        shutil.make_archive(path, "zip", path)
        return images[-1], path, grid_path

    elif mode == "img2img":
       
        path, grid_path = img2img_infer(
            input_image=image_path,
            input_prompt=prompt,
            model=model,
            config = config,
            input_strength=strength,
            seed_num=seed_num,
            n_samples=num_samples,
            n_iter=n_iter,
        )
        shutil.make_archive(path, "zip", path)
        images = glob.glob(grid_path + "/*.png")
        return images[-1], path, grid_path
        
    elif mode == "upscaling":
        path = inference(image_path,prompt,seed_num,scale,steps,eta,num_samples,sampler=model)
        shutil.make_archive(path, "zip", path)
        return  path




def load_model_from_config(config, ckpt, verbose=False):
    print(f"Loading model from {ckpt}")
    pl_sd = torch.load(ckpt, map_location="cpu")
    if "global_step" in pl_sd:
        print(f"Global Step: {pl_sd['global_step']}")
    sd = pl_sd["state_dict"]
    model = instantiate_from_config(config.model)
    m, u = model.load_state_dict(sd, strict=False)
    if len(m) > 0 and verbose:
        print("missing keys:")
        print(m)
    if len(u) > 0 and verbose:
        print("unexpected keys:")
        print(u)

    model.cuda()
    model.eval()
    return model

def load_model(model=None):
    if model == "txt2img":
        config = OmegaConf.load("configs/stable-diffusion/v2-inference-v.yaml")
        model = load_model_from_config(config, "storage/model_weights/diff2/model_v2_768.ckpt")
        model = torch.compile(model)
        return model, config
    elif model == "upscaling":
        model = initialize_model("configs/stable-diffusion/x4-upscaling.yaml", "storage/model_weights/diff2/x4-upscaler-ema.ckpt")
        return model, None
    


