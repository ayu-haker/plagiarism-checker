import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  getDocuments,
  getScans,
  uploadDocument,
  startScan,
  deleteDocument,
  deleteScan,
  Document,
  Scan,
} from '../services/api'

export default function Dashboard() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [scans, setScans] = useState<Scan[]>([])
  const [uploading, setUploading] = useState(false)
  const [scanning, setScanning] = useState<number | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [docs, scanList] = await Promise.all([getDocuments(), getScans()])
      setDocuments(docs)
      setScans(scanList)
    } catch (err) {
      console.error('Failed to load data:', err)
    }
  }

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      await uploadDocument(file)
      await loadData()
    } catch (err) {
      alert('Upload failed. Check the file format.')
    }
    setUploading(false)
    if (fileRef.current) fileRef.current.value = ''
  }

  const handleScan = async (docId: number) => {
    setScanning(docId)
    try {
      const result = await startScan(docId)
      navigate(`/scan/${result.scan_id}`)
    } catch (err) {
      alert('Scan failed.')
    }
    setScanning(null)
  }

  const handleDeleteDoc = async (docId: number) => {
    if (!confirm('Delete this document and all its scans?')) return
    try {
      await deleteDocument(docId)
      await loadData()
    } catch (err) {
      alert('Failed to delete document.')
    }
  }

  const handleDeleteScan = async (scanId: number, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm('Delete this scan?')) return
    try {
      await deleteScan(scanId)
      await loadData()
    } catch (err) {
      alert('Failed to delete scan.')
    }
  }

  const scoreColor = (score: number) => {
    if (score < 15) return 'text-green-600 bg-green-50'
    if (score < 40) return 'text-yellow-600 bg-yellow-50'
    if (score < 70) return 'text-orange-600 bg-orange-50'
    return 'text-red-600 bg-red-50'
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Documents</h2>
        <label className="cursor-pointer">
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.docx,.txt"
            className="hidden"
            onChange={handleUpload}
          />
          <span className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition">
            {uploading ? 'Uploading...' : 'Upload Document'}
          </span>
        </label>
      </div>

      <div className="bg-white rounded-xl shadow-sm border overflow-x-auto">
        <table className="w-full min-w-[700px]">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-6 py-3 text-sm font-medium text-gray-500 w-[40%]">File</th>
              <th className="text-left px-6 py-3 text-sm font-medium text-gray-500">Type</th>
              <th className="text-left px-6 py-3 text-sm font-medium text-gray-500">Words</th>
              <th className="text-left px-6 py-3 text-sm font-medium text-gray-500">Uploaded</th>
              <th className="text-right px-6 py-3 text-sm font-medium text-gray-500 whitespace-nowrap">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {documents.map((doc) => (
              <tr key={doc.id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <div className="font-medium truncate max-w-[320px]" title={doc.filename}>
                    {doc.filename}
                  </div>
                </td>
                <td className="px-6 py-4">
                  <span className="px-2 py-1 text-xs rounded-full bg-gray-100 uppercase">
                    {doc.file_type}
                  </span>
                </td>
                <td className="px-6 py-4 text-gray-600">{doc.word_count.toLocaleString()}</td>
                <td className="px-6 py-4 text-gray-500 text-sm">
                  {new Date(doc.created_at).toLocaleDateString()}
                </td>
                <td className="px-6 py-4 text-right space-x-2 whitespace-nowrap">
                  <button
                    onClick={() => handleScan(doc.id)}
                    disabled={scanning === doc.id}
                    className="px-3 py-1.5 text-sm bg-primary-50 text-primary-700 rounded-lg hover:bg-primary-100 disabled:opacity-50"
                  >
                    {scanning === doc.id ? 'Scanning...' : 'Scan'}
                  </button>
                  <button
                    onClick={() => handleDeleteDoc(doc.id)}
                    className="px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 rounded-lg"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
            {documents.length === 0 && (
              <tr>
                <td colSpan={5} className="px-6 py-12 text-center text-gray-400">
                  No documents yet. Upload a PDF, DOCX, or TXT file to get started.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {scans.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-4">Scan History</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {scans.map((scan) => (
              <div
                key={scan.id}
                onClick={() => navigate(`/scan/${scan.id}`)}
                className="bg-white rounded-xl shadow-sm border p-5 cursor-pointer hover:shadow-md transition relative group"
              >
                <button
                  onClick={(e) => handleDeleteScan(scan.id, e)}
                  className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg"
                  title="Delete scan"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium truncate pr-8">{scan.filename}</h4>
                  <span
                    className={`px-2 py-1 text-sm font-bold rounded-lg ${scoreColor(
                      scan.similarity_score
                    )}`}
                  >
                    {scan.similarity_score.toFixed(1)}%
                  </span>
                </div>
                <div className="flex space-x-4 text-xs text-gray-500">
                  <span className="px-2 py-1 bg-blue-50 text-blue-700 rounded">
                    Web: {scan.web_matches}
                  </span>
                  <span className="px-2 py-1 bg-purple-50 text-purple-700 rounded">
                    Academic: {scan.academic_matches}
                  </span>
                  <span
                    className={`px-2 py-1 rounded ${
                      scan.status === 'completed'
                        ? 'bg-green-50 text-green-700'
                        : scan.status === 'failed'
                        ? 'bg-red-50 text-red-700'
                        : 'bg-yellow-50 text-yellow-700'
                    }`}
                  >
                    {scan.status}
                  </span>
                </div>
                <div className="text-xs text-gray-400 mt-2">
                  {new Date(scan.created_at).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
