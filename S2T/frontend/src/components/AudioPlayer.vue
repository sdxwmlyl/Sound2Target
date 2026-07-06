<template>
  <div class="audio-player">
    <el-button-group>
      <el-button @click="play" :disabled="!ready">
        <el-icon><VideoPlay /></el-icon>
      </el-button>
      <el-button @click="pause" :disabled="!playing">
        <el-icon><VideoPause /></el-icon>
      </el-button>
      <el-button @click="stop" :disabled="!ready">
        <el-icon><CircleClose /></el-icon>
      </el-button>
    </el-button-group>
    
    <div class="time-display">
      {{ formatTime(currentTime) }} / {{ formatTime(duration) }}
    </div>
    
    <el-slider
      v-model="currentPosition"
      :max="100"
      @change="seek"
      class="progress-slider"
    />
    
    <el-slider
      v-model="volume"
      :max="100"
      @change="setVolume"
      class="volume-slider"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { VideoPlay, VideoPause, CircleClose } from '@element-plus/icons-vue'

const props = defineProps({
  audioUrl: String
})

const audio = ref(null)
const ready = ref(false)
const playing = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const volume = ref(80)
const currentPosition = computed(() => duration.value > 0 ? (currentTime.value / duration.value) * 100 : 0)

onMounted(() => {
  if (props.audioUrl) {
    initAudio()
  }
})

onUnmounted(() => {
  if (audio.value) {
    audio.value.pause()
    audio.value = null
  }
})

watch(() => props.audioUrl, (url) => {
  if (url) initAudio()
})

function initAudio() {
  audio.value = new Audio(props.audioUrl)
  audio.value.volume = volume.value / 100
  
  audio.value.addEventListener('loadedmetadata', () => {
    duration.value = audio.value.duration
    ready.value = true
  })
  
  audio.value.addEventListener('timeupdate', () => {
    currentTime.value = audio.value.currentTime
  })
  
  audio.value.addEventListener('ended', () => {
    playing.value = false
  })
}

function play() {
  if (audio.value) {
    audio.value.play()
    playing.value = true
  }
}

function pause() {
  if (audio.value) {
    audio.value.pause()
    playing.value = false
  }
}

function stop() {
  if (audio.value) {
    audio.value.pause()
    audio.value.currentTime = 0
    currentTime.value = 0
    playing.value = false
  }
}

function seek(val) {
  if (audio.value && duration.value > 0) {
    audio.value.currentTime = (val / 100) * duration.value
  }
}

function setVolume(val) {
  if (audio.value) {
    audio.value.volume = val / 100
  }
}

function formatTime(seconds) {
  if (!seconds) return '00:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

defineExpose({ play, pause, stop, seekTo: (time) => { if (audio.value) audio.value.currentTime = time } })
</script>

<style scoped>
.audio-player {
  padding: 10px;
}

.time-display {
  text-align: center;
  margin: 10px 0;
  font-size: 14px;
}

.progress-slider {
  margin-bottom: 10px;
}

.volume-slider {
  width: 100px;
}
</style>