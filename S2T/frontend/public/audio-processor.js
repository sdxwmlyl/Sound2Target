class AudioProcessor extends AudioWorkletProcessor {
  constructor() {
    super()
    this.bufferSize = 8000
    this.buffer = new Int16Array(this.bufferSize)
    this.bufferIndex = 0
  }

  process(inputs, outputs, parameters) {
    const input = inputs[0]
    
    if (input && input[0]) {
      const channel = input[0]
      
      for (let i = 0; i < channel.length; i++) {
        const sample = Math.max(-1, Math.min(1, channel[i]))
        this.buffer[this.bufferIndex] = Math.floor(sample * 32767)
        this.bufferIndex++
        
        if (this.bufferIndex >= this.bufferSize) {
          this.port.postMessage(this.buffer.buffer.slice(0))
          this.bufferIndex = 0
        }
      }
    }
    
    return true
  }
}

registerProcessor('audio-processor', AudioProcessor)