<template>
  <div class="hotword-manager">
    <el-input
      v-model="inputWord"
      placeholder="输入热词"
      @keyup.enter="addWord"
    >
      <template #append>
        <el-button @click="addWord">添加</el-button>
      </template>
    </el-input>
    
    <div class="word-list">
      <el-tag
        v-for="(word, index) in words"
        :key="index"
        closable
        @close="removeWord(index)"
        class="word-tag"
      >
        {{ word }}
      </el-tag>
    </div>
    
    <el-button type="primary" @click="saveWords" size="small">
      保存热词配置
    </el-button>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  projectId: Number,
  initialWords: Array
})

const emit = defineEmits(['saved'])

const inputWord = ref('')
const words = ref([])

watch(() => props.initialWords, (val) => {
  words.value = val || []
}, { immediate: true })

function addWord() {
  const word = inputWord.value.trim()
  if (word && !words.value.includes(word)) {
    words.value.push(word)
    inputWord.value = ''
  }
}

function removeWord(index) {
  words.value.splice(index, 1)
}

async function saveWords() {
  const { projectApi } = await import('@/api')
  
  try {
    await projectApi.updateHotwords(props.projectId, words.value)
    ElMessage.success('热词已保存')
    emit('saved', words.value)
  }
  catch (e) {
    ElMessage.error('保存失败')
  }
}
</script>

<style scoped>
.word-list {
  margin-top: 10px;
  margin-bottom: 10px;
}

.word-tag {
  margin: 5px;
}
</style>