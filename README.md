# SecretWallpaper

Hey you 👀
Yeah, you.
Ever wanted a wallpaper that looks totally normal from afar…
but the moment you zoom in… BOOM — thousands of tiny versions of your favorite picture reveal themselves?

Welcome to SecretWallpaper, the sneaky little tool that turns one image into a gorgeous, zoom-friendly mosaic wallpaper.
Small tiles, big magic. ✨

How the Secret Reveals Itself ?
SecretWallpaper takes one image (your crush, your pet, your aesthetic selfie—don’t worry, I won’t tell 😉)
and repeats it hundreds or thousands of times in tiny tiles to create:
- a full 9:16 phone wallpaper
- with high-detail rendering
- that looks smooth normally
- and looks insanely crisp when you zoom in

Basically: a wallpaper with a secret hidden inside.

How to Summon the Magic
1. Clone the Repo

git clone https://github.com/SonaliDuvesh/SecretWallpaper.git
cd SecretWallpaper

2. Put Your Image in the Same Folder and name it as

   myphoto.jpg

SecretWallpaper performs perfectly when you feed it square-shaped images — it loves that 1:1 symmetry.

3. Install Dependencies

pip install pillow tqdm

4. for Final High-Detail Wallpaper

python3 tiny_tile_wallpaper_scaled.py -i myphoto.jpg -o phone_wallpaper_scale3.jpg --tile 48 --out_w 1080 --out_h 1920 --scale 3 --format jpg --jpg_quality 92

5. for Better Zoom (Insanely Sharp)

python3 tiny_tile_wallpaper_scaled.py -i myphoto.jpg -o phone_wallpaper_scale4.jpg --tile 48 --out_w 1080 --out_h 1920 --scale 4 --format jpg --jpg_quality 92
