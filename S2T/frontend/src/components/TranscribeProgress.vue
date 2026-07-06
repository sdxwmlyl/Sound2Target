<template>
  <el-dialog v-model="visible" title="转写进度" width="400px">
    <el-progress 
      :percentage="progress" 
      :status="status"
      :stroke-width="20"
    />
    
    <div class="progress-info">
      <p v-if="status === 'success'">转写完成！</p>
      <p v-else-if="status === 'exception'">转写失败：{{ errorMessage }}</p>
      <p v-else>正在处理中...</p>
      
      <div class="stats" v-if="segmentsCount > 0">
        <span>已识别 {{ segmentsCount }} 个段落</span>
        <span>共 {{ speakersCount }} 位发言人</span>
      </div>
    </div>
    
    <template #footer>
      <el-button @click="visible = false" v-if="status !== ''">关闭</el-button>
      <el-button type="primary" @click="viewResult" v-if="status === 'success'">
        查看结果
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  audioFileId: Number,
  show: Boolean
})

const emit = defineEmits(['update:show', 'completed'])

const router = useRouter()
const visible = computed({
  get: () => props.show,
  set: (val) => emit('update:show', val)
})

const progress = ref(0)
const status = ref('')
const errorMessage = ref('')
const segmentsCount = ref(0)
const speakersCount = ref(0)

watch(() => props.show, async (val) => {
  if (val && props.audioFileId) {
    startPolling()
  }
})

let pollInterval = null

async function startPolling() {
  progress.value = 30
  status.value = ''
  
  const { transcribeApi } = await import('@/api')
  
  pollInterval = setInterval(async () => {
    try {
      const res = await transcribeApi.getAudioFile(props.audioFileId)
      const data = res.data
      
      if (data.status === 'completed') {
        progress.value = 100
        status.value = 'success'
        clearInterval(pollInterval)
        
        const transcriptRes = await transcribeApi.getTranscript(props.audioFileId)
        segmentsCount.value = transcriptRes.data.segments.length
        const speakers = new Set(transcriptRes.data.segments.map(s => s.speaker_id))
        speakersCount.value = speakers.size
        
        emit('completed', props.audioFileId)
      }
      else if (data.status === 'failed') {
        progress.value = 100
        status.value = 'exception'
        errorMessage.value = data.error_message || '未知错误'
        clearInterval(pollInterval)
      }
      else if (data.status === 'processing') {
        progress.value = Math.min(progress.value + 10, 90)
      }
    }
    catch (e) {
      console.error('Polling error:', e)
    }
  }, 3000)
}

function viewResult() {
  visible.value = false
  router.push(`/transcript/${props.audioFileId}`)
}

function cleanup() {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

watch(visible, (val) => {
  if (!val) cleanup()
})
</script>

<style scoped>
.progress-info {
  margin-top: 20px;
  text-align: center;
}

.stats {
  margin-top: 10px;
  display: flex;
  justify-content: center;
  gap: 20px;
  color: #409eff;
}
</style>