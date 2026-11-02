import subprocess


def make_thumbnail(filename: str) -> None:
    """Render a thumbnail for an uploaded report."""
    subprocess.run(f"convert {filename} -resize 200x200 {filename}.png", shell=True, check=True)
