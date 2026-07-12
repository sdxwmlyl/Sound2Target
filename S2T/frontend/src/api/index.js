import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 300000
})

export const projectApi = {
  list: () => api.get('/projects'),
  get: (id) => api.get(`/projects/${id}`),
  create: (data) => api.post('/projects', data),
  update: (id, data) => api.put(`/projects/${id}`, data),
  delete: (id) => api.delete(`/projects/${id}`),
  updateHotwords: (id, hotwords) => api.put(`/projects/${id}/hotwords`, { hotwords }),
  getAudioFiles: (id) => api.get(`/projects/${id}/audio-files`),
  upload: (projectId, audioName, file) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('audio_name', audioName)
    return api.post(`/projects/${projectId}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  downloadUrl: (projectId, url, audioName) =>
    api.post(`/projects/${projectId}/download-url`, { url, audio_name: audioName })
}

export const audioApi = {
  get: (id) => api.get(`/audio-files/${id}`),
  getTranscript: (id) => api.get(`/audio-files/${id}/transcript`),
  updateSegment: (id, text) => api.put(`/transcript-segments/${id}`, { text }),
  stop: (id) => api.post(`/audio-files/${id}/stop`),
  delete: (id) => api.delete(`/audio-files/${id}`)
}

export const transcribeApi = {
  start: (audioFileId, hotwords, enableDiarization = true) => 
    api.post('/transcribe', { audio_file_id: audioFileId, hotwords, enable_diarization: enableDiarization }),
  getAudioFile: (id) => api.get(`/audio-files/${id}`),
  getTranscript: (id) => api.get(`/audio-files/${id}/transcript`),
  getSessionAudioFiles: (sessionId) => api.get(`/sessions/${sessionId}/audio-files`),
  updateSegment: (id, text) => api.put(`/transcript-segments/${id}`, { text })
}

export const llmApi = {
  summarize: async (audioFileId, prompt, onToken) => {
    const response = await fetch('/api/llm/summarize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ audio_file_id: audioFileId, prompt })
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Summarize failed')
    }
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.token) {
              onToken(data.token)
            }
            if (data.done) {
              return
            }
          } catch (e) {
            // ignore parse errors
          }
        }
      }
    }
  },
  
  chat: async (projectId, question, history, onToken) => {
    const response = await fetch('/api/llm/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        project_id: projectId,
        question,
        history: history || null
      })
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Chat failed')
    }
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.token) {
              onToken(data.token)
            }
            if (data.done) {
              return
            }
          } catch (e) {
            // ignore parse errors
          }
        }
      }
    }
  },
  
  getChatHistory: (projectId, limit = 50) => {
    return api.get(`/llm/chat/history/${projectId}?limit=${limit}`)
  }
}

export const configApi = {
  get: () => api.get('/config')
}

export const audioDeviceApi = {
  getDevices: () => api.get('/audio/devices')
}

export default api