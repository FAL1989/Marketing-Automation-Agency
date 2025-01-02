import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { UserSettings as UserSettingsType, MFASetupResponse } from '../../types';
import { getUserSettings, updateUserSettings } from '../../services/userService';
import { enableMFA, verifyMFA, disableMFA, setRecoveryEmail } from '../../services/mfaService';
import { CheckCircleIcon } from '@heroicons/react/24/outline';
import QRCode from 'qrcode.react';

export const UserSettings: React.FC = () => {
  const navigate = useNavigate();
  const [settings, setSettings] = useState<UserSettingsType>({
    theme: 'light',
    language: 'pt-BR',
    notifications: {
      email: true,
      push: true,
      frequency: 'daily'
    },
    defaultTemplate: null,
    aiProvider: 'openai',
    security: {
      mfaEnabled: false,
      sessionTimeout: 30
    }
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [section, setSection] = useState<'profile' | 'notifications' | 'preferences' | 'security'>('profile');
  const [mfaSetup, setMfaSetup] = useState<MFASetupResponse | null>(null);
  const [verificationCode, setVerificationCode] = useState('');
  const [showMFADialog, setShowMFADialog] = useState(false);
  const [mfaError, setMfaError] = useState<string | null>(null);

  useEffect(() => {
    const loadSettings = async () => {
      try {
        setLoading(true);
        const data = await getUserSettings();
        setSettings(data);
        setError(null);
      } catch (err) {
        console.error('Erro ao carregar configurações:', err);
        setError('Erro ao carregar configurações. Por favor, tente novamente.');
      } finally {
        setLoading(false);
      }
    };

    loadSettings();
  }, []);

  const handleSave = async () => {
    try {
      setSaving(true);
      await updateUserSettings(settings);
      setError(null);
    } catch (err) {
      console.error('Erro ao salvar configurações:', err);
      setError('Erro ao salvar configurações. Por favor, tente novamente.');
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (field: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleNotificationChange = (field: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      notifications: {
        ...prev.notifications,
        [field]: value
      }
    }));
  };

  const handleSecurityChange = (field: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      security: {
        ...prev.security,
        [field]: value
      }
    }));
  };

  const handleEnableMFA = async () => {
    try {
      setMfaError(null);
      const response = await enableMFA();
      setMfaSetup(response);
      setShowMFADialog(true);
    } catch (err) {
      console.error('Erro ao habilitar MFA:', err);
      setMfaError('Erro ao habilitar MFA. Por favor, tente novamente.');
    }
  };

  const handleVerifyMFA = async () => {
    try {
      setMfaError(null);
      await verifyMFA(verificationCode);
      setSettings(prev => ({
        ...prev,
        security: {
          ...prev.security,
          mfaEnabled: true
        }
      }));
      setShowMFADialog(false);
      setMfaSetup(null);
      setVerificationCode('');
    } catch (err) {
      console.error('Erro ao verificar código MFA:', err);
      setMfaError('Código inválido. Por favor, tente novamente.');
    }
  };

  const handleDisableMFA = async () => {
    try {
      setMfaError(null);
      await disableMFA(verificationCode);
      setSettings(prev => ({
        ...prev,
        security: {
          ...prev.security,
          mfaEnabled: false
        }
      }));
      setVerificationCode('');
    } catch (err) {
      console.error('Erro ao desabilitar MFA:', err);
      setMfaError('Erro ao desabilitar MFA. Por favor, tente novamente.');
    }
  };

  const handleSetRecoveryEmail = async (email: string) => {
    try {
      await setRecoveryEmail(email);
      setSettings(prev => ({
        ...prev,
        security: {
          ...prev.security,
          mfaRecoveryEmail: email
        }
      }));
    } catch (err) {
      console.error('Erro ao definir email de recuperação:', err);
      setError('Erro ao definir email de recuperação. Por favor, tente novamente.');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white shadow rounded-lg">
          {/* Cabeçalho */}
          <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Configurações do Usuário
            </h3>
          </div>

          {/* Navegação */}
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex">
              {['profile', 'notifications', 'preferences', 'security'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setSection(tab as any)}
                  className={`${
                    section === tab
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  } whitespace-nowrap py-4 px-6 border-b-2 font-medium text-sm capitalize`}
                >
                  {tab}
                </button>
              ))}
            </nav>
          </div>

          {/* Conteúdo */}
          <div className="px-4 py-5 sm:p-6">
            {error && (
              <div className="mb-4 rounded-md bg-red-50 p-4">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            {section === 'profile' && (
              <div className="space-y-6">
                <div>
                  <label htmlFor="language" className="block text-sm font-medium text-gray-700">
                    Idioma
                  </label>
                  <select
                    id="language"
                    value={settings.language}
                    onChange={(e) => handleInputChange('language', e.target.value)}
                    className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                  >
                    <option value="pt-BR">Português (Brasil)</option>
                    <option value="en">English</option>
                    <option value="es">Español</option>
                  </select>
                </div>
              </div>
            )}

            {section === 'notifications' && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <span className="flex-grow flex flex-col">
                    <span className="text-sm font-medium text-gray-900">Notificações por Email</span>
                    <span className="text-sm text-gray-500">
                      Receba atualizações sobre suas gerações por email
                    </span>
                  </span>
                  <button
                    type="button"
                    onClick={() => handleNotificationChange('email', !settings.notifications.email)}
                    className={`${
                      settings.notifications.email ? 'bg-indigo-600' : 'bg-gray-200'
                    } relative inline-flex flex-shrink-0 h-6 w-11 border-2 border-transparent rounded-full cursor-pointer transition-colors ease-in-out duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500`}
                  >
                    <span
                      className={`${
                        settings.notifications.email ? 'translate-x-5' : 'translate-x-0'
                      } pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow transform ring-0 transition ease-in-out duration-200`}
                    />
                  </button>
                </div>

                <div className="flex items-center justify-between">
                  <span className="flex-grow flex flex-col">
                    <span className="text-sm font-medium text-gray-900">Notificações Push</span>
                    <span className="text-sm text-gray-500">
                      Receba notificações em tempo real no navegador
                    </span>
                  </span>
                  <button
                    type="button"
                    onClick={() => handleNotificationChange('push', !settings.notifications.push)}
                    className={`${
                      settings.notifications.push ? 'bg-indigo-600' : 'bg-gray-200'
                    } relative inline-flex flex-shrink-0 h-6 w-11 border-2 border-transparent rounded-full cursor-pointer transition-colors ease-in-out duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500`}
                  >
                    <span
                      className={`${
                        settings.notifications.push ? 'translate-x-5' : 'translate-x-0'
                      } pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow transform ring-0 transition ease-in-out duration-200`}
                    />
                  </button>
                </div>

                <div>
                  <label htmlFor="frequency" className="block text-sm font-medium text-gray-700">
                    Frequência de Notificações
                  </label>
                  <select
                    id="frequency"
                    value={settings.notifications.frequency}
                    onChange={(e) => handleNotificationChange('frequency', e.target.value)}
                    className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                  >
                    <option value="realtime">Tempo Real</option>
                    <option value="daily">Diário</option>
                    <option value="weekly">Semanal</option>
                  </select>
                </div>
              </div>
            )}

            {section === 'preferences' && (
              <div className="space-y-6">
                <div>
                  <label htmlFor="theme" className="block text-sm font-medium text-gray-700">
                    Tema
                  </label>
                  <select
                    id="theme"
                    value={settings.theme}
                    onChange={(e) => handleInputChange('theme', e.target.value)}
                    className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                  >
                    <option value="light">Claro</option>
                    <option value="dark">Escuro</option>
                    <option value="system">Sistema</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="aiProvider" className="block text-sm font-medium text-gray-700">
                    Provedor de IA
                  </label>
                  <select
                    id="aiProvider"
                    value={settings.aiProvider}
                    onChange={(e) => handleInputChange('aiProvider', e.target.value)}
                    className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                  >
                    <option value="openai">OpenAI</option>
                    <option value="anthropic">Anthropic</option>
                    <option value="google">Google AI</option>
                  </select>
                </div>
              </div>
            )}

            {section === 'security' && (
              <div className="space-y-6">
                {/* MFA Section */}
                <div className="bg-white shadow sm:rounded-lg">
                  <div className="px-4 py-5 sm:p-6">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                      Autenticação de Dois Fatores (MFA)
                    </h3>
                    <div className="mt-2 max-w-xl text-sm text-gray-500">
                      <p>
                        Adicione uma camada extra de segurança à sua conta usando autenticação de dois fatores.
                      </p>
                    </div>
                    <div className="mt-5">
                      {settings.security.mfaEnabled ? (
                        <div className="space-y-4">
                          <div className="flex items-center text-sm text-green-600">
                            <CheckCircleIcon className="h-5 w-5 mr-2" />
                            MFA está ativado
                          </div>
                          <button
                            type="button"
                            onClick={handleDisableMFA}
                            className="inline-flex items-center px-4 py-2 border border-red-300 shadow-sm text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                          >
                            Desativar MFA
                          </button>
                        </div>
                      ) : (
                        <button
                          type="button"
                          onClick={handleEnableMFA}
                          className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                        >
                          Ativar MFA
                        </button>
                      )}
                    </div>
                  </div>
                </div>

                {/* Recovery Email Section */}
                <div className="bg-white shadow sm:rounded-lg">
                  <div className="px-4 py-5 sm:p-6">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                      Email de Recuperação
                    </h3>
                    <div className="mt-2 max-w-xl text-sm text-gray-500">
                      <p>
                        Configure um email alternativo para recuperação de acesso em caso de perda do dispositivo MFA.
                      </p>
                    </div>
                    <div className="mt-5">
                      <input
                        type="email"
                        value={settings.security.mfaRecoveryEmail || ''}
                        onChange={(e) => handleSecurityChange('mfaRecoveryEmail', e.target.value)}
                        className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                        placeholder="email@exemplo.com"
                      />
                    </div>
                  </div>
                </div>

                {/* Session Timeout Section */}
                <div className="bg-white shadow sm:rounded-lg">
                  <div className="px-4 py-5 sm:p-6">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                      Tempo Limite da Sessão
                    </h3>
                    <div className="mt-2 max-w-xl text-sm text-gray-500">
                      <p>
                        Defina o tempo de inatividade após o qual sua sessão será encerrada automaticamente.
                      </p>
                    </div>
                    <div className="mt-5">
                      <select
                        value={settings.security.sessionTimeout}
                        onChange={(e) => handleSecurityChange('sessionTimeout', parseInt(e.target.value))}
                        className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                      >
                        <option value={15}>15 minutos</option>
                        <option value={30}>30 minutos</option>
                        <option value={60}>1 hora</option>
                        <option value={120}>2 horas</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Rodapé */}
          <div className="px-4 py-3 bg-gray-50 text-right sm:px-6">
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="mr-3 inline-flex justify-center py-2 px-4 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={saving}
              className={`inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 ${
                saving ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              {saving ? 'Salvando...' : 'Salvar'}
            </button>
          </div>
        </div>
      </div>

      {/* MFA Dialog */}
      {showMFADialog && mfaSetup && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center">
          <div className="bg-white rounded-lg p-6 max-w-lg w-full">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Configure a Autenticação de Dois Fatores
            </h3>
            
            <div className="space-y-4">
              <div className="flex justify-center">
                <QRCode value={mfaSetup.qr_uri} size={200} />
              </div>
              
              <p className="text-sm text-gray-500">
                1. Escaneie o código QR com seu aplicativo autenticador (Google Authenticator, Authy, etc.)
              </p>
              
              <div className="bg-yellow-50 p-4 rounded-md">
                <h4 className="text-sm font-medium text-yellow-800 mb-2">
                  Códigos de Backup
                </h4>
                <p className="text-xs text-yellow-700 mb-2">
                  Guarde estes códigos em um lugar seguro. Você precisará deles se perder acesso ao seu dispositivo.
                </p>
                <div className="grid grid-cols-2 gap-2">
                  {mfaSetup.backup_codes.map((code, index) => (
                    <code key={index} className="text-xs bg-yellow-100 p-1 rounded">
                      {code}
                    </code>
                  ))}
                </div>
              </div>
              
              <div>
                <label htmlFor="verificationCode" className="block text-sm font-medium text-gray-700">
                  Código de Verificação
                </label>
                <input
                  type="text"
                  id="verificationCode"
                  value={verificationCode}
                  onChange={(e) => setVerificationCode(e.target.value)}
                  placeholder="Digite o código"
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                />
              </div>
              
              {mfaError && (
                <p className="text-sm text-red-600">{mfaError}</p>
              )}
              
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowMFADialog(false);
                    setMfaSetup(null);
                    setVerificationCode('');
                  }}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  onClick={handleVerifyMFA}
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  Verificar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}; 