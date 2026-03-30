import { NavLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { LayoutDashboard, History, Cpu, Bell } from 'lucide-react'
import { useAppStore } from '../store/appStore'

const navItems = [
  { to: '/', icon: LayoutDashboard, labelKey: 'nav.overview' },
  { to: '/historico', icon: History, labelKey: 'nav.history' },
  { to: '/dispositivos', icon: Cpu, labelKey: 'nav.deviceStatus' },
  { to: '/alertas', icon: Bell, labelKey: 'nav.alerts' },
]

export default function Sidebar() {
  const { t, i18n } = useTranslation()
  const systemStatus = useAppStore((state) => state.systemStatus)
  const simpleMode = useAppStore((state) => state.simpleMode)
  const toggleSimpleMode = useAppStore((state) => state.toggleSimpleMode)

  return (
    <aside className="w-64 h-screen bg-white border-r border-[#e5e7eb] flex flex-col shrink-0">
      <div className="px-6 py-6 border-b border-[#e5e7eb]">
        <p className="font-semibold text-xl text-[#101828]">{t('app.name')}</p>
        <p className="text-sm text-[#6a7282] mt-1">{t('app.subtitle')}</p>
      </div>

      <nav className="flex-1 px-4 py-3 flex flex-col gap-2">
        {navItems.map(({ to, icon: Icon, labelKey }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-2 px-3 h-12 rounded-[14px] text-sm font-medium transition-colors
              ${isActive
                ? 'bg-[#2563eb] text-white shadow-md'
                : 'text-[#4a5565] hover:bg-[#f3f4f6]'
              }`
            }
          >
            <Icon size={20} />
            <span className="whitespace-nowrap">{t(labelKey)}</span>
          </NavLink>
        ))}
      </nav>

      <div className="px-4 py-4 border-t border-[#e5e7eb]">
        <div className="bg-[#f9fafb] rounded-[14px] px-4 py-4">
          <p className="text-xs text-[#6a7282]">{t('systemStatus.label')}</p>
          <div className="flex items-center gap-2 mt-1">
            <span
              className={`size-2 rounded-full ${systemStatus?.online !== false ? 'bg-[#10b981]' : 'bg-[#ef4444]'}`}
            />
            <span className="text-sm font-medium text-[#101828]">
              {systemStatus?.online !== false
                ? t('systemStatus.online')
                : t('systemStatus.offline')}
            </span>
          </div>
        </div>
        <button
          type="button"
          onClick={toggleSimpleMode}
          className={`w-full mt-3 px-3 py-2 rounded-[10px] text-sm font-medium transition-colors border ${
            simpleMode
              ? 'bg-[#2563eb] text-white border-[#2563eb]'
              : 'bg-[#f3f4f6] text-[#4a5565] border-[#e5e7eb] hover:bg-[#e5e7eb]'
          }`}
        >
          <span className="block">{t('settings.simpleMode')}</span>
          <span className={`block text-xs mt-0.5 ${simpleMode ? 'text-[#dbeafe]' : 'text-[#6a7282]'}`}>
            {simpleMode ? t('settings.simpleModeOn') : t('settings.simpleModeOff')}
          </span>
        </button>

        <div className="flex items-center justify-center gap-1 mt-3">
          {(['pt', 'en'] as const).map((lng) => (
            <button
              key={lng}
              onClick={() => i18n.changeLanguage(lng)}
              className={`px-3 py-1.5 text-xs font-medium rounded-[10px] transition-colors ${
                i18n.language === lng
                  ? 'bg-[#2563eb] text-white'
                  : 'text-[#6a7282] hover:bg-[#f3f4f6]'
              }`}
            >
              {lng.toUpperCase()}
            </button>
          ))}
        </div>
      </div>
    </aside>
  )
}
