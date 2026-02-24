import { useState, useRef } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { Upload as UploadIcon, FileText, CheckCircle, XCircle, ArrowLeft } from 'lucide-react';

export default function Upload() {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState([]);
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef(null);
  const { user } = useAuth();
  const navigate = useNavigate();

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files);
    }
  };

  const handleFiles = (newFiles) => {
    const validFiles = Array.from(newFiles).filter(f => 
      f.name.endsWith('.pdf') || f.name.endsWith('.png') || 
      f.name.endsWith('.jpg') || f.name.endsWith('.jpeg')
    );
    setFiles(prev => [...prev, ...validFiles]);
  };

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const uploadFiles = async () => {
    if (files.length === 0) return;
    setUploading(true);
    setResults([]);

    try {
      for (const file of files) {
        const formData = new FormData();
        formData.append('files', file);
        
        try {
          const res = await axios.post('/invoices/upload', formData);
          const invoiceId = res.data.results[0]?.id;
          
          if (invoiceId) {
            const processRes = await axios.post(`/invoices/process/${invoiceId}`);
            setResults(prev => [...prev, { 
              filename: file.name, 
              status: processRes.data.status,
              data: processRes.data.data,
              error: processRes.data.error
            }]);
          }
        } catch (err) {
          setResults(prev => [...prev, { 
            filename: file.name, 
            status: 'failed',
            error: err.message
          }]);
        }
      }
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <Link to="/dashboard" className="flex items-center gap-2 text-gray-600 hover:text-gray-800">
              <ArrowLeft size={20} /> Back
            </Link>
            <h1 className="text-xl font-bold">Invoice Extractor</h1>
          </div>
          <span className="text-gray-600">{user?.username}</span>
        </div>
      </nav>

      <div className="max-w-3xl mx-auto px-4 py-8">
        <h2 className="text-2xl font-bold mb-6">Upload Invoices</h2>

        <div 
          className={`border-2 border-dashed rounded-lg p-8 text-center mb-6 ${
            dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
        >
          <input
            ref={inputRef}
            type="file"
            multiple
            accept=".pdf,.png,.jpg,.jpeg"
            onChange={handleChange}
            className="hidden"
          />
          <UploadIcon className="mx-auto text-gray-400 mb-4" size={48} />
          <p className="text-gray-600 mb-2">Drag and drop your invoices here</p>
          <p className="text-gray-400 text-sm">PDF, PNG, JPG, JPEG (max 50MB)</p>
        </div>

        {files.length > 0 && (
          <div className="bg-white rounded-lg shadow-sm mb-6">
            <div className="p-4 border-b">
              <h3 className="font-semibold">Selected Files ({files.length})</h3>
            </div>
            <div className="divide-y">
              {files.map((file, index) => (
                <div key={index} className="p-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <FileText className="text-gray-400" size={20} />
                    <span>{file.name}</span>
                    <span className="text-gray-400 text-sm">({(file.size / 1024).toFixed(1)} KB)</span>
                  </div>
                  <button onClick={() => removeFile(index)} className="text-red-500 hover:text-red-600">
                    Remove
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {files.length > 0 && (
          <button
            onClick={uploadFiles}
            disabled={uploading}
            className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
          >
            {uploading ? 'Processing...' : 'Upload & Extract'}
          </button>
        )}

        {results.length > 0 && (
          <div className="mt-8">
            <h3 className="text-lg font-semibold mb-4">Results</h3>
            <div className="space-y-3">
              {results.map((result, index) => (
                <div key={index} className="bg-white rounded-lg shadow-sm p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      {result.status === 'completed' ? (
                        <CheckCircle className="text-green-500" size={20} />
                      ) : (
                        <XCircle className="text-red-500" size={20} />
                      )}
                      <span className="font-medium">{result.filename}</span>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs ${
                      result.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {result.status}
                    </span>
                  </div>
                  {result.data && (
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div><span className="text-gray-500">Invoice #:</span> {result.data.invoice_number || '-'}</div>
                      <div><span className="text-gray-500">Date:</span> {result.data.invoice_date || '-'}</div>
                      <div><span className="text-gray-500">Customer:</span> {result.data.customer_name || '-'}</div>
                      <div><span className="text-gray-500">Total:</span> {result.data.invoice_total || '-'}</div>
                    </div>
                  )}
                  {result.error && <p className="text-red-500 text-sm mt-2">{result.error}</p>}
                </div>
              ))}
            </div>
            <button
              onClick={() => { setFiles([]); setResults([]); }}
              className="mt-4 w-full bg-gray-200 text-gray-700 py-2 rounded hover:bg-gray-300"
            >
              Upload More
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
