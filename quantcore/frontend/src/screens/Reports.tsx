import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { FileText, Download, Mail, Plus, Calendar, ToggleLeft, ToggleRight, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'
import { useTradingStore } from '@/store/tradingStore'
import { reportsApi } from '@/hooks/useApi'

const REPORT_TYPES = [
  { id: 'daily', label: 'Daily Summary', schedule: '07:00 EST', icon: '📅', delivery: ['Email', 'Dashboard'] },
  { id: 'weekly', label: 'Weekly Deep-Dive', schedule: 'Mon 08:00', icon: '📊', delivery: ['PDF', 'Email'] },
  { id: 'monthly', label: 'Monthly P&L Report', schedule: '1st 08:00', icon: '📈', delivery: ['PDF', 'Email', 'SMS'] },
]

export default function Reports() {
  const { selectedAccount } = useTradingStore()
  const [activeToggles, setActiveToggles] = useState<Set<string>>(new Set(['daily']))
  const [generating, setGenerating] = useState<string | null>(null)

  const { data: reports = [] } = useQuery({
    queryKey: ['reports', selectedAccount?.id],
    queryFn: () => reportsApi.list(selectedAccount!.id).then((r) => r.data.reports || []),
    enabled: !!selectedAccount,
  })

  const generate = async (type: string) => {
    if (!selectedAccount) return
    setGenerating(type)
    try {
      await reportsApi.generate({
        account_id: selectedAccount.id,
        report_type: type,
        delivery: ['dashboard', 'email'],
      })
      toast.success(`${type} report queued for generation`)
    } catch {
      toast.error('Failed to generate report')
    } finally {
      setGenerating(null)
    }
  }

  const toggleReport = (id: string) =>
    setActiveToggles((s) => {
      const n = new Set(s)
      n.has(id) ? n.delete(id) : n.add(id)
      return n
    })

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Automated Reporting Center</h1>
        <button className="flex items-center gap-2 border border-brand-700 text-brand-400 hover:bg-brand-900/30 rounded-lg px-3 py-1.5 text-xs transition-colors">
          <Plus size={12} /> Custom Report
        </button>
      </div>

      {/* Scheduled reports */}
      <div className="glass rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-800 text-xs font-medium text-slate-400">
          Scheduled Reports
        </div>
        <div className="divide-y divide-slate-800">
          {REPORT_TYPES.map((rt) => (
            <div key={rt.id} className="px-4 py-3 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-lg">{rt.icon}</span>
                <div>
                  <div className="text-sm font-medium">{rt.label}</div>
                  <div className="text-xs text-slate-500 flex gap-2 mt-0.5">
                    <span className="flex items-center gap-1"><Calendar size={10} /> {rt.schedule}</span>
                    <span>{rt.delivery.join(' · ')}</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => generate(rt.id)}
                  disabled={generating === rt.id}
                  className="flex items-center gap-1.5 text-xs border border-slate-700 hover:border-slate-500 rounded-lg px-2.5 py-1 transition-colors disabled:opacity-50"
                >
                  {generating === rt.id ? (
                    <RefreshCw size={10} className="animate-spin" />
                  ) : (
                    <FileText size={10} />
                  )}
                  Generate Now
                </button>
                <button onClick={() => toggleReport(rt.id)}>
                  {activeToggles.has(rt.id) ? (
                    <ToggleRight className="text-brand-500" size={20} />
                  ) : (
                    <ToggleLeft className="text-slate-600" size={20} />
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent reports */}
      <div className="glass rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-800 text-xs font-medium text-slate-400">
          Recent Reports
        </div>
        {reports.length === 0 ? (
          <div className="px-4 py-8 text-center text-slate-600 text-sm">
            No reports generated yet. Click "Generate Now" to create your first report.
          </div>
        ) : (
          <div className="divide-y divide-slate-800">
            {reports.map((r: any) => (
              <div key={r.id} className="px-4 py-3 flex items-center justify-between">
                <div>
                  <div className="text-sm">{r.name}</div>
                  <div className="text-xs text-slate-500 mt-0.5">{r.created_at}</div>
                </div>
                <div className="flex gap-2">
                  <button className="text-xs border border-slate-700 rounded px-2 py-1 hover:border-slate-500 transition-colors">View</button>
                  <button className="text-xs border border-slate-700 rounded px-2 py-1 hover:border-slate-500 transition-colors">
                    <Download size={10} className="inline mr-1" />PDF
                  </button>
                  <button className="text-xs border border-slate-700 rounded px-2 py-1 hover:border-slate-500 transition-colors">
                    <Mail size={10} className="inline mr-1" />Resend
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
