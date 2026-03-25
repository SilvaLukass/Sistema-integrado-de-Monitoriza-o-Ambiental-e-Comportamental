import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import pt from './locales/pt/translation.json'
import en from './locales/en/translation.json'

const savedLanguage = localStorage.getItem('language') || 'pt'

i18n
  .use(initReactI18next)
  .init({
    resources: {
      pt: { translation: pt },
      en: { translation: en },
    },
    lng: savedLanguage,
    fallbackLng: 'pt',
    interpolation: {
      escapeValue: false,
    },
  })

i18n.on('languageChanged', (lng) => {
  localStorage.setItem('language', lng)
  document.documentElement.lang = lng
})

document.documentElement.lang = savedLanguage

export default i18n
