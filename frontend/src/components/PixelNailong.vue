<template>
  <canvas
    ref="canvas"
    :width="size"
    :height="size"
    class="pixel-nailong"
  />
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const canvas = ref(null)
const size = 126

const pixelMap = [
  [0,0,0,0,0,0,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0],
  [0,0,0,0,1,1,3,3,3,3,3,2,1,1,0,0,0,0,0,0,0],
  [0,0,0,1,3,3,3,3,2,2,2,2,2,2,1,0,0,0,0,0,0],
  [0,0,1,3,3,2,2,2,2,2,2,2,2,2,2,1,0,0,0,0,0],
  [0,0,1,3,2,2,2,2,2,2,2,2,2,2,2,1,0,0,0,0,0],
  [0,1,0,2,2,2,2,2,2,0,0,0,2,2,2,2,1,0,0,0,0],
  [0,1,7,0,2,2,2,2,0,7,7,0,0,2,2,2,1,0,0,0,0],
  [0,1,7,0,2,2,2,2,0,7,7,4,0,2,2,2,1,0,0,0,0],
  [0,1,4,0,2,2,2,2,0,4,4,4,0,2,2,2,1,0,0,0,0],
  [1,2,0,2,2,2,2,2,2,0,0,0,2,2,2,2,1,0,0,0,0],
  [1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1,0,0,0],
  [1,2,2,2,2,7,7,2,2,2,2,2,2,2,2,2,2,1,0,0,0],
  [1,2,2,2,2,2,2,2,2,2,2,2,2,2,1,2,2,1,0,0,0],
  [0,1,2,2,2,2,2,2,2,2,2,2,2,1,2,2,2,1,0,0,0],
  [0,0,1,1,2,2,2,2,2,2,2,1,1,2,2,2,2,1,0,0,0],
  [0,0,0,0,1,1,1,1,1,1,1,2,2,2,2,2,2,2,1,0,0],
  [0,0,0,1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1,0,0],
  [0,0,0,1,2,3,3,3,3,2,2,2,2,2,2,2,2,2,2,1,0],
  [0,0,1,2,3,3,3,3,3,3,2,2,2,2,1,2,2,2,2,1,0],
  [0,0,1,3,3,3,3,3,3,3,2,2,2,2,1,2,2,2,2,1,0],
  [0,1,1,3,3,3,3,3,3,3,3,2,2,2,2,1,2,2,2,2,1],
  [0,1,1,3,3,3,3,3,3,3,3,3,2,2,2,1,2,2,2,2,1],
  [0,1,3,3,3,3,3,3,3,3,3,3,2,2,2,1,2,2,2,2,1],
  [0,1,3,3,3,3,3,3,3,3,3,3,2,2,2,1,2,2,2,2,1],
  [0,1,3,3,3,3,3,3,3,3,3,3,2,2,2,2,1,2,2,1,0],
  [0,0,1,3,3,3,3,3,3,3,3,2,2,2,2,2,2,1,1,0,0],
  [0,0,1,2,3,3,3,3,3,3,2,2,2,2,2,2,2,1,0,0,0],
  [0,0,1,1,1,2,2,2,2,2,2,2,2,2,2,2,2,1,0,0,0],
  [0,0,0,1,2,1,1,1,1,1,1,2,2,2,2,2,1,0,0,0,0],
  [0,0,0,0,1,2,2,1,0,0,0,1,2,2,2,1,0,0,0,0,0],
  [0,0,0,0,1,1,1,1,0,0,0,1,1,1,1,2,0,0,0,0,0],
]

const colors = {
  0: null,
  1: '#8B5A2B',
  2: '#FFC93C',
  3: '#FFE4B5',
  4: '#4CAF50',
  5: '#1B5E20',
  6: '#FFFFFF',
  7: '#000000',
}

const rows = pixelMap.length
const cols = pixelMap[0].length
const pixelSize = size / rows

const currentX = ref(0)
const currentY = ref(0)
const targetX = ref(0)
const targetY = ref(0)
let animFrame = null

function draw() {
  const ctx = canvas.value.getContext('2d')
  ctx.clearRect(0, 0, size, size)
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const color = colors[pixelMap[r][c]]
      if (color) {
        ctx.fillStyle = color
        ctx.fillRect(c * pixelSize, r * pixelSize, pixelSize, pixelSize)
      }
    }
  }
}

function lerp(a, b, t) {
  return a + (b - a) * t
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value))
}

function animate() {
  currentX.value = lerp(currentX.value, targetX.value, 0.03)
  currentY.value = lerp(currentY.value, targetY.value, 0.03)
  canvas.value.style.left = currentX.value + 'px'
  canvas.value.style.top = currentY.value + 'px'
  animFrame = requestAnimationFrame(animate)
}

function onMouseMove(e) {
  const chatView = document.querySelector('.chat-view')
  if (chatView) {
    const rect = chatView.getBoundingClientRect()
    targetX.value = clamp(e.clientX + 15, rect.left, rect.right - size)
    targetY.value = clamp(e.clientY + 15, rect.top, rect.bottom - size)
  } else {
    targetX.value = e.clientX + 15
    targetY.value = e.clientY + 15
  }
}

onMounted(() => {
  draw()
  const chatView = document.querySelector('.chat-view')
  if (chatView) {
    const rect = chatView.getBoundingClientRect()
    currentX.value = rect.left + rect.width / 2
    currentY.value = rect.top + rect.height / 2
    targetX.value = currentX.value
    targetY.value = currentY.value
  } else {
    currentX.value = window.innerWidth / 2
    currentY.value = window.innerHeight / 2
    targetX.value = currentX.value
    targetY.value = currentY.value
  }
  canvas.value.style.left = currentX.value + 'px'
  canvas.value.style.top = currentY.value + 'px'
  window.addEventListener('mousemove', onMouseMove)
  animFrame = requestAnimationFrame(animate)
})

onUnmounted(() => {
  window.removeEventListener('mousemove', onMouseMove)
  cancelAnimationFrame(animFrame)
})
</script>

<style scoped>
.pixel-nailong {
  position: fixed;
  z-index: 9999;
  pointer-events: none;
  image-rendering: pixelated;
  image-rendering: crisp-edges;
}
</style>
