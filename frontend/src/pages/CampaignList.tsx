import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';
import { Card, CardHeader, CardContent } from '../components/ui/Card';
import { BadgeInfo, CheckCircle, AlertCircle, PlayCircle, Clock } from 'lucide-react';

interface CampaignSummary {
  campaign_id: string;
  subject: string;
  status: string;
  total: number;
  sent: number;
  failed: number;
  created_at: string;
}

const statusIconMap: Record<string, React.ReactNode> = {
  pending: <Clock size={16} className="text-light" />,
  running: <PlayCircle size={16} className="text-black animate-pulse" />,
  completed: <CheckCircle size={16} className="text-success" />,
  partial_failure: <AlertCircle size={16} className="text-error" />,
  auth_error: <AlertCircle size={16} className="text-error" />,
  quota_exceeded: <AlertCircle size={16} className="text-error" />
};

export function CampaignList() {
  const [campaigns, setCampaigns] = useState<CampaignSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await api.get('/campaign/history');
        setCampaigns(res.data);
      } catch (err) {
        console.error('Failed to fetch campaign history', err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchHistory();
  }, []);

  if (isLoading) return <div className="text-center mt-8 text-light">Loading history...</div>;

  return (
    <div className="animate-fade-in" style={{ maxWidth: '800px', margin: '0 auto' }}>
      <h2 className="mb-6 font-semibold" style={{ fontSize: '1.5rem' }}>Campaign History</h2>
      
      {campaigns.length === 0 ? (
        <Card>
          <CardContent className="text-center py-12">
            <BadgeInfo size={32} className="mx-auto text-light mb-4" />
            <p className="text-light">No campaigns found. Start your first job!</p>
          </CardContent>
        </Card>
      ) : (
        <div className="flex flex-col gap-4">
          {campaigns.map((c) => (
            <Link key={c.campaign_id} to={`/campaign/${c.campaign_id}`}>
              <Card className="hover:border-black transition-colors cursor-pointer">
                <CardContent className="flex items-center justify-between p-4">
                  <div>
                    <h3 className="font-semibold mb-1">{c.subject}</h3>
                    <p className="text-xs text-light">
                      Created {new Date(c.created_at).toLocaleString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-6">
                    <div className="text-right">
                      <p className="text-sm">
                        <span className="font-medium text-success">{c.sent}</span> send(s)
                      </p>
                      {c.failed > 0 && <p className="text-xs text-error">{c.failed} fail(s)</p>}
                    </div>
                    <div className="flex flex-col items-center justify-center bg-gray-50 p-2 rounded border" style={{ minWidth: '90px' }}>
                      {statusIconMap[c.status]}
                      <span className="text-xs mt-1 uppercase" style={{ fontSize: '0.65rem' }}>{c.status.replace('_', ' ')}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
