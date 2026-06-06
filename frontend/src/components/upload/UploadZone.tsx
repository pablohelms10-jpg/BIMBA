'use client'

import { useCallback, useState } from 'react'
import { useDropzone, FileRejection } from 'react-dropzone'
import { useRouter } from 'next/navigation'
import { Upload, File, X, CheckCircle, AlertCircle } from 'lucide-react'
import { api } from '@/lib/api'
import { Progress } from '@/components/ui/progress'
import { Button } from '@/components/ui/button'
import { formatFileSize } from '@/lib/utils'
import { cn } from '@/lib/utils'

const ACCEPTED_TYPES: Record<string, string[]> = {
  'video/mp4': ['.mp4'],
  'video/x-msvideo': ['.avi'],
  'video/x-matroska': ['.mkv'],
  'video/quicktime': ['.mov'],
  'audio/mpeg': ['.mp3'],
  'audio/wav': ['.wav'],
  'audio/x-m4a': ['.m4a'],
  'audio/mp4': ['.m4a'],
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'text/plain': ['.txt'],
  'image/jpeg': ['.jpg', '.jpeg'],
  'image/png': ['.png'],
}

type UploadState = 'idle' | 'uploading' | 'success' | 'error'

export function UploadZone() {
  const router = useRouter()
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadState, setUploadState] = useState<UploadState>('idle')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: FileRejection[]) => {
    if (rejectedFiles.length > 0) {
      const msg = rejectedFiles[0]?.errors[0]?.message ?? 'Formato no soportado'
      setErrorMessage(msg)
      return
    }
    if (acceptedFiles.length > 0) {
      setSelectedFile(acceptedFiles[0])
      setErrorMessage(null)
      setUploadState('idle')
      setUploadProgress(0)
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxFiles: 1,
    maxSize: 500 * 1024 * 1024, // 500 MB
  })

  const handleUpload = async () => {
    if (!selectedFile) return
    setUploadState('uploading')
    setErrorMessage(null)
    try {
      const doc = await api.documents.upload(selectedFile, (pct) => {
        setUploadProgress(pct)
      })
      setUploadState('success')
      setTimeout(() => {
        router.push(`/documents/${doc.id}`)
      }, 500)
    } catch (err) {
      setUploadState('error')
      setErrorMessage(err instanceof Error ? err.message : 'Error al subir el archivo')
    }
  }

  const handleClear = () => {
    setSelectedFile(null)
    setUploadState('idle')
    setUploadProgress(0)
    setErrorMessage(null)
  }

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={cn(
          'relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-12 text-center transition-all cursor-pointer',
          isDragActive
            ? 'border-[#3b82f6] bg-blue-950/30 scale-[1.01]'
            : selectedFile
            ? 'border-[#10b981] bg-emerald-950/20'
            : 'border-[#1f2937] bg-[#111827]/50 hover:border-[#3b82f6] hover:bg-blue-950/10',
          uploadState === 'error' && 'border-red-700 bg-red-950/20'
        )}
      >
        <input {...getInputProps()} />

        {!selectedFile ? (
          <>
            <div
              className={cn(
                'mb-4 flex h-16 w-16 items-center justify-center rounded-full',
                isDragActive ? 'bg-blue-900/60' : 'bg-[#1f2937]'
              )}
            >
              <Upload className={cn('h-8 w-8', isDragActive ? 'text-[#3b82f6]' : 'text-[#9ca3af]')} />
            </div>
            <p className="text-lg font-semibold text-[#f9fafb]">
              {isDragActive ? 'Suelta el archivo aquí' : 'Arrastra tu archivo aquí'}
            </p>
            <p className="mt-1.5 text-sm text-[#9ca3af]">o haz clic para explorar archivos</p>
            <p className="mt-3 text-xs text-[#9ca3af]">Tamaño máximo: 500 MB</p>
          </>
        ) : (
          <div className="flex flex-col items-center gap-3 w-full max-w-sm" onClick={(e) => e.stopPropagation()}>
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[#1f2937]">
              {uploadState === 'success' ? (
                <CheckCircle className="h-8 w-8 text-[#10b981]" />
              ) : uploadState === 'error' ? (
                <AlertCircle className="h-8 w-8 text-red-400" />
              ) : (
                <File className="h-8 w-8 text-[#3b82f6]" />
              )}
            </div>
            <div className="text-center">
              <p className="text-sm font-medium text-[#f9fafb] truncate max-w-xs">{selectedFile.name}</p>
              <p className="text-xs text-[#9ca3af]">{formatFileSize(selectedFile.size)}</p>
            </div>
            {uploadState === 'uploading' && (
              <div className="w-full">
                <Progress value={uploadProgress} showLabel className="w-full" />
              </div>
            )}
            {uploadState !== 'uploading' && (
              <div className="flex gap-2">
                {uploadState !== 'success' && (
                  <Button onClick={handleUpload} size="md">
                    <Upload className="h-4 w-4" />
                    Subir archivo
                  </Button>
                )}
                <Button onClick={handleClear} variant="ghost" size="md">
                  <X className="h-4 w-4" />
                  Cancelar
                </Button>
              </div>
            )}
          </div>
        )}
      </div>

      {errorMessage && (
        <p className="flex items-center gap-2 text-sm text-red-400">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {errorMessage}
        </p>
      )}
    </div>
  )
}
