import { useState, useEffect, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  humanizeText,
  humanizeFile,
  HumanizeResult,
} from '../services/api'

type Result = (HumanizeResult & { filename?: string; word_count?: number }) | null

export default function Humanizer() {
  const [searchParams] = useSearchParams()
  const [inputText, setInputText] = useState('')
  const [result, setResult] = useState<Result>(null)
  const [mode, setMode] = useState('standard')
  const [loading, setLoading] = useState(false)
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [activeTab, setActiveTab] = useState<'text' | 'file'>('text')
  const [error, setError] = useState('')

  useEffect(() => {
    const text = searchParams.get('text')
    if (text) {
      setInputText(decodeURIComponent(text))
      setActiveTab('text')
    }
  }, [searchParams])

  const handleHumanizeText = async () => {
    if (!inputText.trim()) return
    setLoading(true)
    setError('')
    try {
      const res = await humanizeText(inputText, mode)
      setResult(res)
    } catch (err) {
      setError('Humanization failed. Please try again.')
    }
    setLoading(false)
  }

  const handleHumanizeFile = async () => {
    if (!uploadFile) return
    setLoading(true)
    setError('')
    try {
      const res = await humanizeFile(uploadFile, mode)
      setResult({
        original_text: res.original_text,
        humanized_text: res.humanized_text,
        mode: res.mode,
        meaning_similarity: res.meaning_similarity,
        filename: res.filename,
        word_count: res.word_count,
      })
    } catch (err) {
      setError('Failed to process file. Check the format.')
    }
    setLoading(false)
  }

  const handleDownload = useCallback(() => {
    if (!result?.humanized_text) return
    const blob = new Blob([result.humanized_text], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `humanized_${result.filename || 'document'}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }, [result])

  const handleCopy = () => {
    if (result?.humanized_text) {
      navigator.clipboard.writeText(result.humanized_text)
    }
  }

  const similarityColor = (score: number) => {
    if (score >= 0.7) return 'text-green-600'
    if (score >= 0.5) return 'text-yellow-600'
    return 'text-red-600'
  }

  const similarityBg = (score: number) => {
    if (score >= 0.7) return 'bg-green-500'
    if (score >= 0.5) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Text Humanizer</h2>

      <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg w-fit">
        <button
          onClick={() => setActiveTab('text')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition ${
            activeTab === 'text'
              ? 'bg-white shadow text-primary-700'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Paste Text
        </button>
        <button
          onClick={() => setActiveTab('file')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition ${
            activeTab === 'file'
              ? 'bg-white shadow text-primary-700'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Upload PDF / DOCX / TXT
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          <label className="block text-sm font-medium text-gray-700">
            {activeTab === 'text' ? 'Original Text' : 'Upload File'}
          </label>

          {activeTab === 'text' ? (
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Paste your text here..."
              className="w-full h-72 p-4 border rounded-xl resize-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          ) : (
            <div className="h-72 border-2 border-dashed rounded-xl flex flex-col items-center justify-center bg-gray-50 hover:bg-gray-100 transition cursor-pointer relative">
              <input
                type="file"
                accept=".pdf,.docx,.txt"
                className="absolute inset-0 opacity-0 cursor-pointer"
                onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
              />
              {uploadFile ? (
                <div className="text-center">
                  <div className="text-4xl mb-2">
                    {uploadFile.type === 'application/pdf' ? '📄' : '📝'}
                  </div>
                  <p className="font-medium text-gray-700">{uploadFile.name}</p>
                  <p className="text-sm text-gray-400 mt-1">
                    {(uploadFile.size / 1024).toFixed(1)} KB — click to change
                  </p>
                </div>
              ) : (
                <div className="text-center">
                  <div className="text-4xl mb-2">📁</div>
                  <p className="font-medium text-gray-600">Drop file or click to upload</p>
                  <p className="text-sm text-gray-400 mt-1">PDF, DOCX, or TXT</p>
                </div>
              )}
            </div>
          )}

          <div className="flex items-center space-x-4">
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value)}
              className="px-4 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-primary-500"
            >
              <option value="light">Light — Minor edits (96%+ accuracy)</option>
              <option value="standard">Standard — Balanced (84%+ accuracy)</option>
              <option value="aggressive">Aggressive — Full rewrite</option>
            </select>

            <button
              onClick={activeTab === 'text' ? handleHumanizeText : handleHumanizeFile}
              disabled={loading || (activeTab === 'text' ? !inputText.trim() : !uploadFile)}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition font-medium"
            >
              {loading ? 'Processing...' : 'Humanize'}
            </button>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}
        </div>

        <div className="space-y-4">
          <label className="block text-sm font-medium text-gray-700">
            Humanized Output
          </label>
          {result ? (
            <div className="space-y-3">
              {result.filename && (
                <div className="bg-blue-50 border border-blue-200 text-blue-700 px-4 py-2 rounded-lg text-sm">
                  📄 {result.filename} — {result.word_count?.toLocaleString()} words processed
                </div>
              )}
              <textarea
                readOnly
                value={result.humanized_text}
                className="w-full h-72 p-4 border rounded-xl resize-none bg-green-50 border-green-200 focus:ring-0"
              />
              <div className="flex items-center space-x-3">
                <span className="text-sm text-gray-500">Meaning preserved:</span>
                <span className={`text-sm font-bold ${similarityColor(result.meaning_similarity)}`}>
                  {(result.meaning_similarity * 100).toFixed(1)}%
                </span>
                <div className="flex-1 bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${similarityBg(result.meaning_similarity)}`}
                    style={{ width: `${result.meaning_similarity * 100}%` }}
                  />
                </div>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={handleCopy}
                  className="px-4 py-2 text-sm border rounded-lg hover:bg-gray-50 transition flex-1"
                >
                  📋 Copy
                </button>
                <button
                  onClick={handleDownload}
                  className="px-4 py-2 text-sm border rounded-lg hover:bg-gray-50 transition flex-1"
                >
                  💾 Download .txt
                </button>
              </div>
            </div>
          ) : (
            <div className="w-full h-72 p-4 border rounded-xl bg-gray-50 flex items-center justify-center text-gray-400 text-sm">
              Humanized text will appear here
            </div>
          )}
        </div>
      </div>

      {result && (
        <div className="bg-white rounded-xl shadow-sm border p-5">
          <h3 className="text-lg font-semibold mb-3">Side-by-Side Comparison</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <h4 className="font-medium text-gray-500 mb-2">Original</h4>
              <div className="bg-red-50 p-4 rounded-lg border border-red-100 max-h-64 overflow-y-auto leading-relaxed whitespace-pre-wrap">
                {result.original_text}
              </div>
            </div>
            <div>
              <h4 className="font-medium text-gray-500 mb-2">Humanized</h4>
              <div className="bg-green-50 p-4 rounded-lg border border-green-100 max-h-64 overflow-y-auto leading-relaxed whitespace-pre-wrap">
                {result.humanized_text}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
