import { useState, useEffect, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getScanResult, downloadPdf, deleteScan, ScanMatch, ScanResult } from '../services/api'

export default function ScanResults() {
  const { scanId } = useParams<{ scanId: string }>()
  const [result, setResult] = useState<ScanResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedMatch, setSelectedMatch] = useState<ScanMatch | null>(null)
  const [highlightFilter, setHighlightFilter] = useState<'all' | 'web' | 'academic'>('all')
  const navigate = useNavigate()

  useEffect(() => {
    if (scanId) loadScan(parseInt(scanId))
  }, [scanId])

  const loadScan = async (id: number) => {
    setLoading(true)
    try {
      const data = await getScanResult(id)
      setResult(data)
    } catch (err) {
      console.error('Failed to load scan:', err)
    }
    setLoading(false)
  }

  const filteredHighlights = useMemo(() => {
    if (!result) return []
    if (highlightFilter === 'all') return result.highlights
    return result.highlights.filter((h) => h.type === highlightFilter)
  }, [result, highlightFilter])

  const highlightedHtml = useMemo(() => {
    if (!result?.original_text) return ''
    const text = result.original_text
    if (filteredHighlights.length === 0) return escapeHtml(text)

    const sorted = [...filteredHighlights].sort((a, b) => a.start - b.start)
    let parts: string[] = []
    let lastEnd = 0

    for (const h of sorted) {
      if (h.start > lastEnd) {
        parts.push(escapeHtml(text.slice(lastEnd, h.start)))
      }
      const color =
        h.score >= 0.7
          ? 'bg-red-200 border-b-2 border-red-500'
          : h.score >= 0.4
          ? 'bg-orange-100 border-b-2 border-orange-400'
          : 'bg-yellow-100 border-b border-yellow-400'
      parts.push(
        `<mark class="${color} px-0.5 rounded cursor-pointer hover:opacity-80 transition" data-start="${h.start}" data-end="${h.end}">${escapeHtml(text.slice(h.start, h.end))}</mark>`
      )
      lastEnd = h.end
    }
    if (lastEnd < text.length) {
      parts.push(escapeHtml(text.slice(lastEnd)))
    }
    return parts.join('')
  }, [result, filteredHighlights])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400 flex items-center space-x-2">
          <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span>Loading scan results...</span>
        </div>
      </div>
    )
  }

  if (!result) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Scan not found.</p>
        <button onClick={() => navigate('/')} className="mt-4 text-primary-600 hover:underline">
          Back to Dashboard
        </button>
      </div>
    )
  }

  const scoreColor = (score: number) => {
    if (score < 15) return 'text-green-600'
    if (score < 40) return 'text-yellow-600'
    if (score < 70) return 'text-orange-600'
    return 'text-red-600'
  }

  const scoreBg = (score: number) => {
    if (score < 15) return 'bg-green-500'
    if (score < 40) return 'bg-yellow-500'
    if (score < 70) return 'bg-orange-500'
    return 'bg-red-500'
  }

  const flaggedWords = result.highlights.reduce((sum, h) => {
    return sum + textSlice(result.original_text, h.start, h.end).split(/\s+/).length
  }, 0)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button onClick={() => navigate('/')} className="text-gray-400 hover:text-gray-600">
            ← Back
          </button>
          <h2 className="text-2xl font-bold">{result.filename}</h2>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => downloadPdf(result.id)}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition text-sm font-medium flex items-center space-x-1"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span>Download PDF Report</span>
          </button>
          <button
            onClick={async () => {
              if (!confirm('Delete this scan?')) return
              try {
                await deleteScan(result.id)
                navigate('/')
              } catch (err) {
                alert('Failed to delete scan.')
              }
            }}
            className="px-4 py-2 border text-red-600 rounded-lg hover:bg-red-50 transition text-sm font-medium flex items-center space-x-1"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            <span>Delete</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <div className="bg-white rounded-xl shadow-sm border p-4">
          <div className="text-xs text-gray-500">Similarity</div>
          <div className={`text-2xl font-bold ${scoreColor(result.similarity_score)}`}>
            {result.similarity_score.toFixed(1)}%
          </div>
          <div className="mt-1 w-full bg-gray-200 rounded-full h-1.5">
            <div
              className={`h-1.5 rounded-full ${scoreBg(result.similarity_score)}`}
              style={{ width: `${Math.min(result.similarity_score, 100)}%` }}
            />
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border p-4">
          <div className="text-xs text-gray-500">Flagged Words</div>
          <div className="text-2xl font-bold text-red-600">{flaggedWords}</div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border p-4">
          <div className="text-xs text-gray-500">Total Words</div>
          <div className="text-2xl font-bold">{result.word_count}</div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border p-4">
          <div className="text-xs text-gray-500">Web Sources</div>
          <div className="text-2xl font-bold text-blue-600">{result.web_matches}</div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border p-4">
          <div className="text-xs text-gray-500">Academic</div>
          <div className="text-2xl font-bold text-purple-600">{result.academic_matches}</div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        <div className="px-5 py-3 border-b bg-gray-50 flex items-center justify-between">
          <h3 className="font-semibold">Document with Plagiarism Highlights</h3>
          <div className="flex space-x-2">
            {(['all', 'web', 'academic'] as const).map((f) => (
              <button
                key={f}
                onClick={() => setHighlightFilter(f)}
                className={`px-3 py-1 text-xs rounded-full font-medium transition ${
                  highlightFilter === f
                    ? f === 'web'
                      ? 'bg-blue-100 text-blue-700 ring-1 ring-blue-300'
                      : f === 'academic'
                      ? 'bg-purple-100 text-purple-700 ring-1 ring-purple-300'
                      : 'bg-gray-200 text-gray-700 ring-1 ring-gray-300'
                    : 'bg-white text-gray-500 hover:bg-gray-100 border'
                }`}
              >
                {f === 'all' ? 'All' : f === 'web' ? 'Web' : 'Academic'}
              </button>
            ))}
          </div>
        </div>

        <div className="p-6">
          <div
            className="text-sm leading-relaxed text-gray-800 whitespace-pre-wrap"
            dangerouslySetInnerHTML={{ __html: highlightedHtml }}
          />
        </div>

        <div className="px-5 py-3 border-t bg-gray-50 flex items-center space-x-4 text-xs text-gray-500">
          <span className="flex items-center space-x-1">
            <span className="w-3 h-3 bg-red-200 rounded border-b-2 border-red-500" />
            <span>High match (70%+)</span>
          </span>
          <span className="flex items-center space-x-1">
            <span className="w-3 h-3 bg-orange-100 rounded border-b-2 border-orange-400" />
            <span>Medium match (40-70%)</span>
          </span>
          <span className="flex items-center space-x-1">
            <span className="w-3 h-3 bg-yellow-100 rounded border border-yellow-400" />
            <span>Low match (&lt;40%)</span>
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-3">
          <h3 className="text-lg font-semibold">Match Details ({result.matches.length})</h3>
          {result.matches.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm border p-8 text-center text-gray-400">
              No matches found — this document appears original.
            </div>
          ) : (
            result.matches.map((match) => (
              <div
                key={match.id}
                onClick={() => setSelectedMatch(match)}
                className={`bg-white rounded-xl shadow-sm border p-4 cursor-pointer transition hover:shadow-md ${
                  selectedMatch?.id === match.id ? 'ring-2 ring-primary-500' : ''
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span
                      className={`px-2 py-0.5 text-xs rounded-full font-medium ${
                        match.match_type === 'web'
                          ? 'bg-blue-100 text-blue-700'
                          : 'bg-purple-100 text-purple-700'
                      }`}
                    >
                      {match.match_type}
                    </span>
                    <span className="text-xs text-gray-400">
                      {Math.round(match.similarity_score * 100)}% match
                    </span>
                  </div>
                  <div className="w-16 bg-gray-200 rounded-full h-1.5">
                    <div
                      className={`h-1.5 rounded-full ${
                        match.similarity_score >= 0.7
                          ? 'bg-red-500'
                          : match.similarity_score >= 0.4
                          ? 'bg-orange-400'
                          : 'bg-yellow-400'
                      }`}
                      style={{ width: `${match.similarity_score * 100}%` }}
                    />
                  </div>
                </div>
                <p className="text-sm text-gray-700 line-clamp-2">{match.chunk_text}</p>
                {match.source_title && (
                  <p className="text-xs text-gray-400 mt-2 truncate">
                    Source: {match.source_title}
                  </p>
                )}
              </div>
            ))
          )}
        </div>

        <div className="space-y-4">
          <h3 className="text-lg font-semibold">Source Comparison</h3>
          {selectedMatch ? (
            <div className="bg-white rounded-xl shadow-sm border p-5 space-y-4">
              <div>
                <h4 className="text-sm font-medium text-red-600 mb-1 flex items-center">
                  <span className="w-2 h-2 bg-red-500 rounded-full mr-1" />
                  Your Text
                </h4>
                <p className="text-sm bg-red-50 p-3 rounded-lg border border-red-100 leading-relaxed">
                  {selectedMatch.chunk_text}
                </p>
              </div>
              <div>
                <h4 className="text-sm font-medium text-blue-600 mb-1 flex items-center">
                  <span className="w-2 h-2 bg-blue-500 rounded-full mr-1" />
                  Matched Source
                </h4>
                <p className="text-sm bg-blue-50 p-3 rounded-lg border border-blue-100 leading-relaxed">
                  {selectedMatch.source_text}
                </p>
              </div>
              {selectedMatch.source_url && (
                <div>
                  <h4 className="text-sm font-medium text-gray-500 mb-1">Source URL</h4>
                  <a
                    href={selectedMatch.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-primary-600 hover:underline break-all"
                  >
                    {selectedMatch.source_url}
                  </a>
                </div>
              )}
              <div className="pt-2 flex space-x-2">
                <button
                  onClick={() => {
                    const encoded = encodeURIComponent(selectedMatch.chunk_text)
                    navigate(`/humanizer?text=${encoded}`)
                  }}
                  className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition text-sm"
                >
                  Humanize This Text
                </button>
                {selectedMatch.source_url && (
                  <a
                    href={selectedMatch.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-4 py-2 border rounded-lg hover:bg-gray-50 transition text-sm text-gray-600"
                  >
                    Visit Source
                  </a>
                )}
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-xl shadow-sm border p-5 text-center text-gray-400 text-sm">
              Click a match to see source comparison
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

function textSlice(text: string, start: number, end: number): string {
  return text.slice(Math.max(0, start), Math.min(end, text.length))
}
