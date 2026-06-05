import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Eye, EyeOff, TrendingUp, AlertCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import { authApi } from '@/hooks/useApi'
import { useAuthStore } from '@/store/authStore'

const schema = z.object({
  email: z.string().email('Valid email required'),
  password: z.string().min(1, 'Password required'),
  remember: z.boolean().optional(),
  totpCode: z.string().optional(),
})
type FormData = z.infer<typeof schema>

export default function Login() {
  const navigate = useNavigate()
  const { setTokens } = useAuthStore()
  const [showPass, setShowPass] = useState(false)
  const [needsTotp, setNeedsTotp] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (data: FormData) => {
    setIsLoading(true)
    try {
      const { data: res } = await authApi.login(data.email, data.password)
      if (res.totp_required && !data.totpCode) {
        setNeedsTotp(true)
        setIsLoading(false)
        return
      }
      if (needsTotp && data.totpCode) {
        await authApi.verifyTOTP(data.totpCode)
      }
      setTokens(res.access_token, res.refresh_token)
      navigate('/dashboard')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Login failed')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-surface-950 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-2">
            <TrendingUp className="text-brand-500" size={32} />
            <span className="text-2xl font-bold text-white">QuantCore AI</span>
          </div>
          <p className="text-slate-400 text-sm">Institutional-grade automated trading</p>
        </div>

        <div className="glass rounded-2xl p-8">
          <h1 className="text-xl font-semibold mb-6">Sign in to your account</h1>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">Email</label>
              <input
                {...register('email')}
                type="email"
                className="w-full bg-surface-900 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand-500 transition-colors"
                placeholder="you@example.com"
              />
              {errors.email && <p className="text-red-400 text-xs mt-1">{errors.email.message}</p>}
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-1">Password</label>
              <div className="relative">
                <input
                  {...register('password')}
                  type={showPass ? 'text' : 'password'}
                  className="w-full bg-surface-900 border border-slate-700 rounded-lg px-3 py-2 pr-10 text-sm focus:outline-none focus:border-brand-500 transition-colors"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPass(!showPass)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                >
                  {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              {errors.password && <p className="text-red-400 text-xs mt-1">{errors.password.message}</p>}
            </div>

            {needsTotp && (
              <div>
                <label className="block text-sm text-slate-400 mb-1">Authenticator Code</label>
                <input
                  {...register('totpCode')}
                  type="text"
                  maxLength={6}
                  className="w-full bg-surface-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-center tracking-widest focus:outline-none focus:border-brand-500 transition-colors"
                  placeholder="000000"
                />
              </div>
            )}

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 text-sm text-slate-400 cursor-pointer">
                <input {...register('remember')} type="checkbox" className="rounded" />
                Remember me
              </label>
              <Link to="/forgot-password" className="text-sm text-brand-500 hover:text-brand-400">
                Forgot password?
              </Link>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-brand-600 hover:bg-brand-500 disabled:opacity-50 rounded-lg py-2.5 text-sm font-medium transition-colors"
            >
              {isLoading ? 'Signing in…' : 'Sign In'}
            </button>
          </form>

          <div className="mt-4 flex items-center gap-3">
            <div className="flex-1 h-px bg-slate-700" />
            <span className="text-xs text-slate-500">or continue with</span>
            <div className="flex-1 h-px bg-slate-700" />
          </div>

          <div className="mt-4 grid grid-cols-3 gap-2">
            {['Google', 'Microsoft', 'Apple'].map((provider) => (
              <button
                key={provider}
                className="border border-slate-700 rounded-lg py-2 text-xs text-slate-400 hover:border-slate-500 hover:text-slate-200 transition-colors"
              >
                {provider}
              </button>
            ))}
          </div>

          <p className="text-center text-sm text-slate-500 mt-6">
            No account?{' '}
            <Link to="/register" className="text-brand-500 hover:text-brand-400">
              Create one
            </Link>
          </p>
        </div>

        <div className="flex items-center gap-1.5 justify-center mt-4 text-xs text-slate-600">
          <AlertCircle size={12} />
          <span>Secured with AES-256 encryption and TLS 1.3</span>
        </div>
      </div>
    </div>
  )
}
