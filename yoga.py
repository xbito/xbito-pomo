import random

desk_yoga_stretches = [
    "Sit up straight in your chair with your feet flat on the floor. Raise your arms overhead and interlace your fingers, then turn your palms up toward the ceiling. Stretch your arms up and hold for 10-15 seconds, then release.",
    "Sit on the edge of your chair with your feet flat on the floor. Place your right ankle on your left knee, forming a figure four. Gently press down on your right knee and lean forward slightly, feeling the stretch in your hip. Hold for 10-15 seconds, then switch sides.",
    "Sit up straight in your chair with your feet flat on the floor. Place your left hand on the back of your chair and twist your torso to the left, looking over your left shoulder. Hold for 10-15 seconds, then switch sides.",
    "Sit up straight in your chair with your feet flat on the floor. Extend your right arm across your body and use your left hand to gently press your right arm closer to your chest. Hold for 10-15 seconds, then switch sides.",
    "Sit up straight in your chair with your feet flat on the floor. Drop your right ear toward your right shoulder, feeling the stretch along the left side of your neck. Hold for 10-15 seconds, then switch sides.",
]


def get_desk_yoga_stretch():
    return random.choice(desk_yoga_stretches)
