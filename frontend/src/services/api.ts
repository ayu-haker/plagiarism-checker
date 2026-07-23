import axios from 'axios'

const API_BASE = '/api'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
})

export interface Document {
  id: number
  filename: string
  file_type: string
  word_count: number
  created_at: string
}

export interface Scan {
  id: number
  document_id: number
  filename: string
  status: string
  similarity_score: number
  web_matches: number
  academic_matches: number
  created_at: string
}

export interface ScanMatch {
  id: number
  chunk_text: string
  source_text: string
  source_url: string | null
  source_title: string | null
  similarity_score: number
  match_type: string
  start_position: number
  end_position: number
}

export interface Highlight {
  start: number
  end: number
  text: string
  score: number
  type: string
}

export interface ScanResult extends Scan {
  completed_at: string | null
  original_text: string
  word_count: number
  highlights: Highlight[]
  matches: ScanMatch[]
}

export interface HumanizeResult {
  original_text: string
  humanized_text: string
  mode: string
  meaning_similarity: number
}

export const uploadDocument = async (file: File): Promise<Document> => {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post('/documents/upload', formData)
  return data
}

export const getDocuments = async (): Promise<Document[]> => {
  const { data } = await api.get('/documents/')
  return data
}

export const getDocument = async (id: number): Promise<Document & { text_content: string }> => {
  const { data } = await api.get(`/documents/${id}`)
  return data
}

export const deleteDocument = async (id: number): Promise<void> => {
  await api.delete(`/documents/${id}`)
}

export const startScan = async (docId: number): Promise<{ scan_id: number; status: string; similarity_score: number }> => {
  const { data } = await api.post(`/scans/${docId}/scan`)
  return data
}

export const getScans = async (): Promise<Scan[]> => {
  const { data } = await api.get('/scans/')
  return data
}

export const getScanResult = async (scanId: number): Promise<ScanResult> => {
  const { data } = await api.get(`/scans/${scanId}`)
  return data
}

export const deleteScan = async (scanId: number): Promise<void> => {
  await api.delete(`/scans/${scanId}`)
}

export const downloadPdf = async (scanId: number): Promise<void> => {
  const response = await api.get(`/scans/${scanId}/pdf`, { responseType: 'blob' })
  const blob = new Blob([response.data], { type: 'application/pdf' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `plagiarism_report_${scanId}.pdf`
  a.click()
  URL.revokeObjectURL(url)
}

export const humanizeText = async (text: string, mode: string): Promise<HumanizeResult> => {
  const { data } = await api.post('/humanize/', { text, mode })
  return data
}

export interface HumanizeFileResult {
  filename: string
  original_text: string
  humanized_text: string
  mode: string
  meaning_similarity: number
  word_count: number
}

export const humanizeFile = async (file: File, mode: string): Promise<HumanizeFileResult> => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('mode', mode)
  const { data } = await api.post('/humanize/file', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  })
  return data
}

export const getHumanizeHistory = async () => {
  const { data } = await api.get('/humanize/history')
  return data
}
