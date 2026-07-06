import { defineStore } from 'pinia'
import { ref } from 'vue'
import { projectApi } from '@/api'

export const useProjectStore = defineStore('project', () => {
  const projects = ref([])
  const currentProject = ref(null)
  const loading = ref(false)
  
  async function fetchProjects() {
    loading.value = true
    try {
      const res = await projectApi.list()
      projects.value = res.data
    } finally {
      loading.value = false
    }
  }
  
  async function fetchProject(id) {
    loading.value = true
    try {
      const res = await projectApi.get(id)
      currentProject.value = res.data
      return res.data
    } finally {
      loading.value = false
    }
  }
  
  async function createProject(name, description) {
    const res = await projectApi.create({ name, description })
    await fetchProjects()
    return res.data
  }
  
  async function updateProject(id, data) {
    await projectApi.update(id, data)
    await fetchProjects()
  }
  
  async function deleteProject(id) {
    await projectApi.delete(id)
    await fetchProjects()
  }
  
  return {
    projects,
    currentProject,
    loading,
    fetchProjects,
    fetchProject,
    createProject,
    updateProject,
    deleteProject
  }
})