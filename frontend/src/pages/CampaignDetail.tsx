import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../api';
import { Card, CardHeader, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { DownloadCloud, ArrowLeft, RefreshCw } from 'lucide-react';
import { Link } from 'react-router-dom';

interface CampaignDetailData {
  campaign_id: string;
  subject: string;
  status: string;
  total: number;
  sent: number;
  failed: number;
  pending: number;
}

interface LogEntry {
  id: string;
  recipient_name: string;
  recipient_email: string;
  status: string;
  error_detail: string | null;
  sent_at: string | null;
}

export function CampaignDetail() {
  const { id } = useParams<{ id: string }>();
  
  const [detail, setDetail] = useState<CampaignDetailData | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [isLoading, setIsLoading] = useState(true);

  // Combine fetch manually for polling capability
  const fetchAllData = async () => {
    if (!id) return;
    try {
      const [statusRes, logsRes] = await Promise.all([
        api.get(`/campaign/${id}`),
        api.get(`/campaign/${id}/logs?page=${page}&page_size=30`)
      ]);
      setDetail(statusRes.data);
      setLogs(logsRes.data.logs);
      setTotalPages(Math.ceil(logsRes.data.total / 30));
    } catch (err) {
      console.error('Failed to fetch detail', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAllData();
  }, [id, page]);

  useEffect(() => {
    // Poll every 3 seconds if status is running
    if (detail?.status === 'running') {
      const interval = setInterval(() => {
        fetchAllData();
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [detail?.status, id, page]);

  if (isLoading && !detail) return <div className="text-center mt-8 text-light">Loading details...</div>;
  if (!detail) return <div className="text-center mt-8 text-error">Campaign not found</div>;

  const handleExport = () => {
    window.location.href = `http://localhost:8000/api/v1/campaign/${id}/export`;
  };

  const progressPercent = detail.total > 0 ? ((detail.sent + detail.failed) / detail.total) * 100 : 0;

  return (
    <div className="animate-fade-in" style={{ maxWidth: '900px', margin: '0 auto' }}>
      <div className="flex justify-between items-center mb-6">
        <Link to="/history" className="text-sm text-light hover:text-black flex items-center gap-1">
          <ArrowLeft size={16} /> Back to History
        </Link>
        <Button variant="outline" size="sm" onClick={handleExport}>
          <DownloadCloud size={16} style={{marginRight: '8px'}}/> Export CSV
        </Button>
      </div>

      <Card className="mb-6">
        <CardContent className="p-6">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h2 className="font-semibold text-xl mb-1">{detail.subject}</h2>
              <p className="text-sm text-light uppercase tracking-wider">{detail.status.replace('_', ' ')}</p>
            </div>
            {detail.status === 'running' && (
              <div className="flex items-center gap-2 text-sm font-medium bg-gray-50 border px-3 py-1 rounded">
                <RefreshCw size={14} className="animate-spin" /> In Progress
              </div>
            )}
          </div>
          
          <div className="w-full bg-gray-200 h-2 rounded-full overflow-hidden mb-4">
            <div 
              className="bg-black h-full transition-all duration-500" 
              style={{ width: `${progressPercent}%` }} 
            />
          </div>

          <div className="flex justify-between text-sm text-center border-t border-gray-100 pt-4 mt-4">
            <div className="flex-1 border-r border-gray-100">
              <span className="block text-2xl font-semibold">{detail.total}</span>
              <span className="text-xs text-light">Total</span>
            </div>
            <div className="flex-1 border-r border-gray-100">
              <span className="block text-2xl font-semibold text-success">{detail.sent}</span>
              <span className="text-xs text-light">Sent</span>
            </div>
            <div className="flex-1 border-r border-gray-100">
              <span className="block text-2xl font-semibold text-error">{detail.failed}</span>
              <span className="text-xs text-light">Failed</span>
            </div>
            <div className="flex-1">
              <span className="block text-2xl font-semibold">{detail.pending}</span>
              <span className="text-xs text-light">Pending</span>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="mb-4 flex justify-between items-center">
        <h3 className="font-semibold" style={{ fontSize: '1.2rem' }}>Logs</h3>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" disabled={page === 1} onClick={() => setPage(p => p - 1)}>Prev</Button>
          <span className="text-sm text-light">Page {page} of {totalPages || 1}</span>
          <Button variant="ghost" size="sm" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Next</Button>
        </div>
      </div>

      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-50 text-xs text-light border-b" style={{ borderColor: 'var(--color-border)' }}>
                <th className="p-3 font-medium">Recipient</th>
                <th className="p-3 font-medium">Status</th>
                <th className="p-3 font-medium hidden sm:table-cell">Time</th>
                <th className="p-3 font-medium">Details</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id} className="border-b text-sm max-h-16" style={{ borderColor: 'var(--color-border)' }}>
                  <td className="p-3">
                    <span className="block font-medium">{log.recipient_name || 'N/A'}</span>
                    <span className="text-xs text-light">{log.recipient_email}</span>
                  </td>
                  <td className="p-3">
                    <span className={`inline-block px-2 py-1 rounded text-xs lowercase ${
                      log.status === 'sent' ? 'bg-green-50 text-green-700' :
                      log.status === 'failed' ? 'bg-red-50 text-red-700' :
                      'bg-gray-100 text-gray-700'
                    }`}>
                      {log.status}
                    </span>
                  </td>
                  <td className="p-3 text-xs text-light hidden sm:table-cell">
                    {log.sent_at ? new Date(log.sent_at).toLocaleTimeString() : '-'}
                  </td>
                  <td className="p-3 text-xs text-error max-w-[200px] truncate" title={log.error_detail || ''}>
                    {log.error_detail || '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
