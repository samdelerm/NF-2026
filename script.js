const joystickPad = document.getElementById("joystickPad");
const joystickKnob = document.getElementById("joystickKnob");

const deadZone = 0.16;
const activeState = {
  pointerId: null,
  intensity: 0,
};

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function getDirectionFromVector(x, y) {
  const magnitude = Math.hypot(x, y);
  if (magnitude < deadZone) {
    return { direction: null, intensity: 0 };
  }

  const angle = Math.atan2(-y, x) * (180 / Math.PI);
  if (angle >= -45 && angle < 45) {
    return { direction: "droite", intensity: magnitude };
  }
  if (angle >= 45 && angle < 135) {
    return { direction: "haut", intensity: magnitude };
  }
  if (angle >= -135 && angle < -45) {
    return { direction: "bas", intensity: magnitude };
  }

  return { direction: "gauche", intensity: magnitude };
}

function setKnobPosition(x, y) {
  joystickKnob.style.transform = `translate(calc(-50% + ${x}px), calc(-50% + ${y}px))`;
}

function resetJoystick() {
  activeState.pointerId = null;
  activeState.intensity = 0;
  setKnobPosition(0, 0);
}

joystickPad.addEventListener("pointerdown", (event) => {
  joystickPad.setPointerCapture(event.pointerId);
  activeState.pointerId = event.pointerId;
  updateJoystick(event);
});

joystickPad.addEventListener("pointermove", (event) => {
  if (activeState.pointerId !== event.pointerId) {
    return;
  }

  updateJoystick(event);
});

joystickPad.addEventListener("pointerup", (event) => {
  if (activeState.pointerId !== event.pointerId) {
    return;
  }

  resetJoystick();
});

joystickPad.addEventListener("pointercancel", resetJoystick);

function updateJoystick(event) {
  const rect = joystickPad.getBoundingClientRect();
  const centerX = rect.width / 2;
  const centerY = rect.height / 2;
  const maxRadius = rect.width * 0.28;
  const offsetX = event.clientX - rect.left - centerX;
  const offsetY = event.clientY - rect.top - centerY;
  const distance = Math.hypot(offsetX, offsetY);
  const limitedDistance = clamp(distance, 0, maxRadius);
  const angle = Math.atan2(offsetY, offsetX);
  const x = Math.cos(angle) * limitedDistance;
  const y = Math.sin(angle) * limitedDistance;
  const normalizedX = x / maxRadius;
  const normalizedY = y / maxRadius;
  const state = getDirectionFromVector(normalizedX, normalizedY);

  activeState.intensity = state.intensity;

  setKnobPosition(x, y);
}

window.addEventListener("keydown", (event) => {
  const keyMap = {
    ArrowUp: "haut",
    ArrowDown: "bas",
    ArrowLeft: "gauche",
    ArrowRight: "droite",
  };

  const direction = keyMap[event.key];
  if (!direction) {
    return;
  }

  event.preventDefault();
  activeState.intensity = 1;
  const offset = 48;
  const movement = {
    haut: { x: 0, y: -offset },
    bas: { x: 0, y: offset },
    gauche: { x: -offset, y: 0 },
    droite: { x: offset, y: 0 },
  }[direction];
  setKnobPosition(movement.x, movement.y);
});