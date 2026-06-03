<template>
  <div class="tree-node">
    <div 
      class="node-content" 
      :class="{ 
        folder: node.isFolder, 
        'is-selected': !node.isFolder && isSelected,
        'is-folder-expanded': node.isFolder && isExpanded
      }"
      :style="{ paddingLeft: (node.level * 20) + 'px' }"
    >
      <!-- Кнопка сворачивания/разворачивания для папок -->
      <div 
        v-if="node.isFolder" 
        class="node-toggle" 
        @click="handleFolderToggle"
      >
        {{ isExpanded ? '▼' : '▶' }}
      </div>
      <div v-else class="node-toggle-placeholder"></div>

      <!-- Чекбокс для файлов -->
      <input 
        v-if="!node.isFolder"
        type="checkbox" 
        :checked="isSelected"
        @change="handleFileToggle"
        class="file-checkbox"
      />
      <div v-else class="folder-checkbox-placeholder"></div>

      <!-- Иконка -->
      <span class="node-icon">
        {{ node.isFolder ? (isExpanded ? '📂' : '📁') : getFileIcon(node.name) }}
      </span>
      
      <!-- Название -->
      <span class="node-name" @click="node.isFolder ? handleFolderToggle() : null">
        {{ node.name }}
      </span>
      
      <!-- Размер -->
      <span v-if="!node.isFolder" class="node-size">{{ formatSize(node.file?.size || 0) }}</span>
      <span v-else class="node-size folder-size">
        {{ formatSize(node.size) }}
      </span>
    </div>

    <!-- Дочерние элементы -->
    <div v-if="node.isFolder && isExpanded && node.children" class="node-children">
      <FileTreeNode 
        v-for="child in node.children" 
        :key="child.path"
        :node="child"
        :selected-files="selectedFiles"
        :expanded-folders="expandedFolders"
        @toggle-file="$emit('toggle-file', $event)"
        @toggle-folder="$emit('toggle-folder', $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  node: any
  selectedFiles: Set<string>
  expandedFolders: Record<string, boolean> 
}>()

const emit = defineEmits<{
  'toggle-file': [path: string]
  'toggle-folder': [path: string]
}>()

const isSelected = computed(() => {
  return !props.node.isFolder && props.selectedFiles.has(props.node.path)
})

const isExpanded = computed(() => {
  if (!props.node.isFolder) return false
  return props.expandedFolders[props.node.path] === true
})

function handleFileToggle() {
  if (!props.node.isFolder) {
    emit('toggle-file', props.node.path)
  }
}

function handleFolderToggle() {
  if (props.node.isFolder) {
    emit('toggle-folder', props.node.path)
  }
}

function getFileIcon(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase()
  const icons: Record<string, string> = {
    'js': '📜', 'ts': '📘', 'vue': '🟢', 'py': '🐍',
    'java': '☕', 'cpp': '💠', 'c': '📘', 'cs': '💚',
    'php': '🐘', 'rb': '💎', 'go': '🔷', 'rs': '🦀',
    'sql': '🗄', 'html': '🌐', 'css': '🎨', 'json': '📋',
    'yaml': '📝', 'yml': '📝', 'md': '📄', 'txt': '📃',
    'dockerfile': '🐳', 'sh': '🐚', 'aspx': '', 'sln': ''
  }
  return icons[ext || ''] || '📄'
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}
</script>

<style scoped>
.tree-node {
  user-select: none;
}

.node-content {
  display: flex;
  align-items: center;
  padding: 6px 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  margin: 2px 0;
}

.node-content:hover {
  background: #edf2f7;
}

.node-content.folder {
  font-weight: 600;
  color: #4a5568;
}

.node-content.is-selected {
  background: #e6fffa;
  border-left: 3px solid #48bb78;
}

.node-content.is-folder-expanded {
  background: #ebf8ff;
}

.node-toggle {
  width: 20px;
  text-align: center;
  font-size: 0.7rem;
  color: #718096;
  cursor: pointer;
  transition: transform 0.2s;
}

.node-toggle-placeholder {
  width: 20px;
}

.folder-checkbox-placeholder {
  width: 16px;
  margin-right: 8px;
}

.file-checkbox {
  margin-right: 8px;
  cursor: pointer;
  width: 16px;
  height: 16px;
}

.node-icon {
  margin-right: 8px;
  font-size: 1.1rem;
  min-width: 24px;
  text-align: center;
}

.node-name {
  flex: 1;
  font-size: 0.9rem;
  word-break: break-all;
}

.node-name:hover {
  text-decoration: underline;
}

.node-size {
  font-size: 0.75rem;
  color: #a0aec0;
  white-space: nowrap;
  margin-left: 12px;
}

.folder-size {
  font-style: italic;
}

.node-children {
  margin-left: 0;
  border-left: 1px dashed #cbd5e0;
  padding-left: 8px;
}
</style>