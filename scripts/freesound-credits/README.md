# Freesound Credits Generator

Open an editorial file, look for sound strips and collect their credit
and license from Freesound using the API.

- Generate an API token https://freesound.org/apiv2/apply
- Export FREESOUND_API_KEY with a freesound API token
- Run Blender with Python script that outputs the credits file

```plaintext
export FREESOUND_API_KEY=<the key>
<blender> <filename> --background --factory-startup --python generate_sound_credits.py
```
