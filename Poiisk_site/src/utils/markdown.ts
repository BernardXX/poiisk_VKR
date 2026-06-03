import { marked } from 'marked'
import DOMPurify from 'dompurify'

export function parseMarkdown(text: string): string {
  if (!text) return ''
  // breaks: true превращает переносы строк в <br>
  const rawHtml = marked.parse(text, { breaks: true }) as string
  // Очищаем от опасных скриптов
  return DOMPurify.sanitize(rawHtml)
}