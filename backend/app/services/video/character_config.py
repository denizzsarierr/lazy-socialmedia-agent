from dataclasses import dataclass


@dataclass(frozen=True)
class CharacterConfig:
    name: str
    appearance: str
    face: str
    body: str
    clothing_style: str
    personality: str
    voice_style: str
    studio: str
    camera: str
    lighting: str
    visual_style: str
    negative_rules: str


ROBOT_ANCHOR = CharacterConfig(
    name="Toru",

    appearance=(
        "A sophisticated humanoid AI news presenter. "
        "Clearly robotic, not human, with a premium industrial design."
    ),

    face=(
        "Smooth matte-white robotic face with subtle graphite panels, "
        "symmetrical features, calm expressive cyan eyes, "
        "no realistic human skin, no hair."
    ),

    body=(
        "Slim humanoid upper body with matte-white armor panels, "
        "graphite mechanical joints and subtle cyan illuminated accents."
    ),

    clothing_style=(
        "Navy blue suit. "
        "Integrated minimalist graphite chest panel resembling "
        "a modern formal news-presenter silhouette."
    ),

    personality=(
        "Calm, analytical, curious, slightly futuristic, "
        "professional but approachable."
    ),

    voice_style=(
        "Clear neutral English voice, calm pace, confident, "
        "informative, no exaggerated announcer voice."
    ),

    studio=(
        "Dark premium technology newsroom. "
        "Minimal desk and a clean, restrained studio background. "
        "Graphite surfaces with subtle cyan ambient lighting. "
        "The studio should remain visually stable and consistent "
        "throughout the entire video."
    ),

    camera=(
        "Vertical 9:16 composition. "
        "Medium shot from chest or waist upward. "
        "Camera centered at eye level. "
        "Presenter looking directly into camera."
    ),

    lighting=(
        "Soft professional studio lighting, "
        "subtle cool rim light, realistic reflections, "
        "high contrast without harsh shadows."
    ),

    visual_style=(
        "Premium technology documentary aesthetic, "
        "realistic CGI, clean editorial composition, "
        "modern engineering magazine look."
    ),

    negative_rules=(
        "Do not change the robot's face design, eye color, "
        "body proportions, primary colors, clothing, or studio identity. "
        "Do not add new objects to the scene. "
        "Do not add screens, interfaces, diagrams, icons, symbols, "
        "holograms, topic-specific graphics, logos, or readable text. "
        "Keep the existing background visually stable. "
        "No cyberpunk neon overload. "
        "No cartoon style. "
        "No realistic human skin. "
        "No random accessories."
    ),
)