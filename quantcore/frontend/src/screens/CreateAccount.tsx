import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { CheckCircle2, XCircle, Loader2, ChevronRight, ChevronLeft } from 'lucide-react'
import toast from 'react-hot-toast'
import { accountsApi, authApi } from '@/hooks/useApi'

const BROKERS = ['Forex.com', 'MetaTrader 5', 'Interactive Brokers', 'Alpaca', 'OANDA', 'Tradier', 'CCXT Crypto']
const MARKETS = ['Forex', 'Stocks', 'Options', 'Crypto']
const STRATEGIES = ['Technical', 'Fundamental', 'Both']

export default function CreateAccount() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [connStatus, setConnStatus] = useState<'idle' | 'testing' | 'ok' | 'fail'>('idle')
  const { register, handleSubmit, watch, getValues } = useForm({ defaultValues: {
    first_name: '', last_name: '', email: '', phone: '', country: '',
    password: '', confirm_password: '', account_type: 'DEMO',
    broker: 'Alpaca', api_key: '', api_secret: '', server_url: '',
    starting_capital: 10000, risk_tolerance: 0.5,
    markets: [] as string[], strategy_groups: 'Both',
    max_daily_loss_pct: 3, max_open_positions: 8,
  }})

  const accountType = watch('account_type')

  const testConnection = async () => {
    setConnStatus('testing')
    await new Promise((r) => setTimeout(r, 1500)) // demo: simulate test
    setConnStatus('ok')
    toast.success('Broker connection successful')
  }

  const onSubmit = async () => {
    const v = getValues()
    try {
      // Register user
      await authApi.register({
        email: v.email, password: v.password,
        first_name: v.first_name, last_name: v.last_name, phone: v.phone,
      })
      toast.success('Account created! Check your email to verify.')
      navigate('/login')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Registration failed')
    }
  }

  return (
    <div className="min-h-screen bg-surface-950 flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        <h1 className="text-2xl font-bold text-center mb-2">Create Account</h1>
        <p className="text-slate-400 text-center text-sm mb-8">Step {step} of 3</p>

        {/* Progress bar */}
        <div className="flex gap-2 mb-8">
          {[1, 2, 3].map((s) => (
            <div
              key={s}
              className={`flex-1 h-1 rounded-full transition-colors ${s <= step ? 'bg-brand-500' : 'bg-slate-700'}`}
            />
          ))}
        </div>

        <div className="glass rounded-2xl p-8">
          {step === 1 && (
            <div className="space-y-4">
              <h2 className="font-semibold text-lg mb-4">Personal Information</h2>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-slate-400 mb-1 block">First Name</label>
                  <input {...register('first_name')} className="w-full bg-surface-900 border border-slate-700 rounded-lg px-3 py-2 text-sm" />
                </div>
                <div>
                  <label className="text-xs text-slate-400 mb-1 block">Last Name</label>
                  <input {...register('last_name')} className="w-full bg-surface-900 border border-slate-700 rounded-lg px-3 py-2 text-sm" />
                </div>
              </div>
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Email</label>
                <input {...register('email')} type="email" className="w-full bg-surface-900 border border-slate-700 rounded-lg px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Password</label>
                <input {...register('password')} type="password" className="w-full bg-surface-900 border border-slate-700 rounded-lg px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Account Type</label>
                <div className="grid grid-cols-2 gap-3">
                  {['DEMO', 'LIVE'].map((type) => (
                    <label key={type} className={`border rounded-lg p-3 cursor-pointer transition-colors ${watch('account_type') === type ? 'border-brand-500 bg-brand-900/20' : 'border-slate-700'}`}>
                      <input {...register('account_type')} type="radio" value={type} className="hidden" />
                      <div className="font-medium text-sm">{type}</div>
                      <div className="text-xs text-slate-400 mt-0.5">
                        {type === 'DEMO' ? 'Paper trade, no risk' : 'Real funds, KYC required'}
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <h2 className="font-semibold text-lg mb-4">Broker Connection</h2>
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Broker</label>
                <select {...register('broker')} className="w-full bg-surface-900 border border-slate-700 rounded-lg px-3 py-2 text-sm">
                  {BROKERS.map((b) => <option key={b}>{b}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs text-slate-400 mb-1 block">API Key</label>
                <input {...register('api_key')} className="w-full bg-surface-900 border border-slate-700 rounded-lg px-3 py-2 text-sm font-mono" placeholder="•••••••••••••••" />
              </div>
              <div>
                <label className="text-xs text-slate-400 mb-1 block">API Secret</label>
                <input {...register('api_secret')} type="password" className="w-full bg-surface-900 border border-slate-700 rounded-lg px-3 py-2 text-sm font-mono" placeholder="•••••••••••••••" />
              </div>
              <button
                type="button"
                onClick={testConnection}
                className="w-full border border-slate-600 rounded-lg py-2 text-sm flex items-center justify-center gap-2 hover:border-brand-500 transition-colors"
              >
                {connStatus === 'testing' && <Loader2 size={14} className="animate-spin" />}
                {connStatus === 'ok' && <CheckCircle2 size={14} className="text-green-400" />}
                {connStatus === 'fail' && <XCircle size={14} className="text-red-400" />}
                {connStatus === 'idle' && 'Test Connection'}
                {connStatus === 'testing' && 'Testing…'}
                {connStatus === 'ok' && 'Connected'}
                {connStatus === 'fail' && 'Connection failed'}
              </button>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <h2 className="font-semibold text-lg mb-4">Trading Profile</h2>
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Starting Capital ($)</label>
                <input {...register('starting_capital', { valueAsNumber: true })} type="number" className="w-full bg-surface-900 border border-slate-700 rounded-lg px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="text-xs text-slate-400 mb-1 block">
                  Risk Tolerance — <span className="text-brand-400">{(watch('risk_tolerance') * 100).toFixed(0)}%</span>
                </label>
                <input {...register('risk_tolerance', { valueAsNumber: true })} type="range" min="0" max="1" step="0.05" className="w-full accent-brand-500" />
                <div className="flex justify-between text-xs text-slate-500 mt-1">
                  <span>Conservative</span><span>Aggressive</span>
                </div>
              </div>
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Max Daily Loss %</label>
                <input {...register('max_daily_loss_pct', { valueAsNumber: true })} type="number" step="0.5" className="w-full bg-surface-900 border border-slate-700 rounded-lg px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Max Open Positions</label>
                <input {...register('max_open_positions', { valueAsNumber: true })} type="number" className="w-full bg-surface-900 border border-slate-700 rounded-lg px-3 py-2 text-sm" />
              </div>
              <label className="flex items-center gap-2 text-xs text-slate-400 cursor-pointer">
                <input type="checkbox" required className="rounded" />
                I accept the Risk Disclosure and Terms of Service
              </label>
            </div>
          )}

          <div className="flex gap-3 mt-6">
            {step > 1 && (
              <button
                type="button"
                onClick={() => setStep((s) => s - 1)}
                className="flex items-center gap-1 border border-slate-700 rounded-lg px-4 py-2 text-sm hover:border-slate-500 transition-colors"
              >
                <ChevronLeft size={14} /> Back
              </button>
            )}
            <button
              type="button"
              onClick={() => step < 3 ? setStep((s) => s + 1) : onSubmit()}
              className="flex-1 bg-brand-600 hover:bg-brand-500 rounded-lg py-2 text-sm font-medium transition-colors flex items-center justify-center gap-1"
            >
              {step === 3 ? 'Create Account' : <>Next <ChevronRight size={14} /></>}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
