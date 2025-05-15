import React, { useState, useEffect } from 'react';
import { 
  Settings, 
  User, 
  Bell, 
  Shield, 
  Palette, 
  Moon, 
  Sun, 
  Check, 
  Smartphone, 
  Globe, 
  Info, 
  Save, 
  CheckCircle2,
  RefreshCw,
  Sliders,
  Languages,
  Brush,
  Code,
  Laptop,
  Lock,
  CreditCard,
  Database,
  Network,
  HelpCircle,
  Mail,
  Phone,
  Camera,
  Upload,
  Edit3,
  Building,
  MapPin,
  Download,
  TrendingUp,
  Clock
} from 'lucide-react';
import { cn } from '../lib/utils';
import { useAuth } from '../contexts/AuthContext';
import { UserProfile, saveUserProfile, getUserProfile } from '../services/userService';
import { toast } from 'sonner';
import { supabase } from '../lib/supabaseClient';

// Define tab types for better type safety
type SettingsTab = 'cuenta' | 'seguridad';

const SettingsPage = () => {
  const { user } = useAuth();
  // Active tab state
  const [activeTab, setActiveTab] = useState<SettingsTab>('cuenta');
  
  // Theme states
  const [theme, setTheme] = useState<'light' | 'dark' | 'system'>('system');
  const [accentColor, setAccentColor] = useState<string>('violet');
  const [animationsEnabled, setAnimationsEnabled] = useState<boolean>(true);
  const [reduceMotion, setReduceMotion] = useState<boolean>(false);
  const [compactMode, setCompactMode] = useState<boolean>(false);
  
  // User profile states
  const [userName, setUserName] = useState<string>('');
  const [userEmail, setUserEmail] = useState<string>('');
  const [userPhone, setUserPhone] = useState<string>('');
  const [userCompany, setUserCompany] = useState<string>('');
  const [userLocation, setUserLocation] = useState<string>('');
  const [userBio, setUserBio] = useState<string>('');
  
  // Notification states
  const [emailNotifications, setEmailNotifications] = useState<boolean>(true);
  const [pushNotifications, setPushNotifications] = useState<boolean>(true);
  const [tradingAlerts, setTradingAlerts] = useState<boolean>(true);
  const [newsUpdates, setNewsUpdates] = useState<boolean>(false);
  const [criticalAlertsEnabled, setCriticalAlertsEnabled] = useState<boolean>(true);
  const [soundsEnabled, setSoundsEnabled] = useState<boolean>(true);
  
  // User preferences
  const [language, setLanguage] = useState<string>('es-LA');
  const [timeFormat, setTimeFormat] = useState<'12h' | '24h'>('24h');
  const [currency, setCurrency] = useState<string>('USD');
  const [dateFormat, setDateFormat] = useState<string>('DD/MM/YYYY');
  const [timezone, setTimezone] = useState<string>('America/Mexico_City');

  // API Settings
  const [apiKey, setApiKey] = useState<string>('sk_live_xxxxxxxxxxxxxxxxxxxxx');
  const [showApiKey, setShowApiKey] = useState<boolean>(false);
  const [webhookUrl, setWebhookUrl] = useState<string>('https://example.com/webhook');
  const [apiRateLimit, setApiRateLimit] = useState<number>(100);
  
  // Security settings
  const [twoFactorEnabled, setTwoFactorEnabled] = useState<boolean>(false);
  const [sessionTimeout, setSessionTimeout] = useState<number>(30);
  const [ipWhitelisting, setIpWhitelisting] = useState<boolean>(false);
  const [loginNotifications, setLoginNotifications] = useState<boolean>(true);
  
  // Advanced settings
  const [enableBetaFeatures, setEnableBetaFeatures] = useState<boolean>(false);
  const [telemetryEnabled, setTelemetryEnabled] = useState<boolean>(true);
  const [dataExportFormat, setDataExportFormat] = useState<string>('JSON');
  
  // Settings saved state
  const [settingsSaved, setSettingsSaved] = useState<boolean>(false);

  // New states for password change
  const [currentPassword, setCurrentPassword] = useState<string>('');
  const [newPassword, setNewPassword] = useState<string>('');
  const [confirmPassword, setConfirmPassword] = useState<string>('');
  const [passwordError, setPasswordError] = useState<string>('');
  const [passwordSuccess, setPasswordSuccess] = useState<boolean>(false);
  
  // New email change states
  const [newEmail, setNewEmail] = useState<string>('');
  const [emailChangeSuccess, setEmailChangeSuccess] = useState<boolean>(false);
  
  // Loading states
  const [isLoading, setIsLoading] = useState<boolean>(false);
  
  // Fetch user profile on mount
  useEffect(() => {
    if (user?.id) {
      fetchUserProfile(user.id);
    }
  }, [user]);
  
  // Fetch user profile from Supabase
  const fetchUserProfile = async (userId: string) => {
    try {
      setIsLoading(true);
      const profile = await getUserProfile(userId);
      
      if (profile) {
        // Populate states with profile data
        setUserName(profile.name || '');
        setUserEmail(profile.email || user?.email || '');
        setUserPhone(profile.phone || '');
        setUserCompany(profile.company || '');
        setUserLocation(profile.location || '');
        setUserBio(profile.bio || '');
        
        // Theme settings
        setTheme(profile.theme || 'system');
        setAccentColor(profile.accent_color || 'violet');
        setAnimationsEnabled(profile.animations_enabled !== undefined ? profile.animations_enabled : true);
        setReduceMotion(profile.reduce_motion || false);
        setCompactMode(profile.compact_mode || false);
        
        // Notifications
        setEmailNotifications(profile.email_notifications !== undefined ? profile.email_notifications : true);
        setPushNotifications(profile.push_notifications !== undefined ? profile.push_notifications : true);
        setTradingAlerts(profile.trading_alerts !== undefined ? profile.trading_alerts : true);
        setNewsUpdates(profile.news_updates || false);
        setCriticalAlertsEnabled(profile.critical_alerts_enabled !== undefined ? profile.critical_alerts_enabled : true);
        setSoundsEnabled(profile.sounds_enabled !== undefined ? profile.sounds_enabled : true);
        
        // Preferences
        setLanguage(profile.language || 'es-LA');
        setTimeFormat(profile.time_format || '24h');
        setCurrency(profile.currency || 'USD');
        setDateFormat(profile.date_format || 'DD/MM/YYYY');
        setTimezone(profile.timezone || 'America/Mexico_City');
        
        // Security
        setTwoFactorEnabled(profile.two_factor_enabled || false);
        setSessionTimeout(profile.session_timeout || 30);
        setIpWhitelisting(profile.ip_whitelisting || false);
        setLoginNotifications(profile.login_notifications !== undefined ? profile.login_notifications : true);
      } else {
        // Set default values if no profile exists
        if (user?.email) {
          setUserEmail(user.email);
        }
      }
    } catch (error) {
      console.error('Error al cargar el perfil:', error);
      toast.error('No se pudo cargar tu perfil.');
    } finally {
      setIsLoading(false);
    }
  };

  // Toggle functions
  const toggleEmailNotifications = () => setEmailNotifications(!emailNotifications);
  const togglePushNotifications = () => setPushNotifications(!pushNotifications);
  const toggleTradingAlerts = () => setTradingAlerts(!tradingAlerts);
  const toggleNewsUpdates = () => setNewsUpdates(!newsUpdates);
  const toggleTwoFactor = () => setTwoFactorEnabled(!twoFactorEnabled);
  const toggleAnimations = () => setAnimationsEnabled(!animationsEnabled);
  const toggleReduceMotion = () => setReduceMotion(!reduceMotion);
  const toggleCompactMode = () => setCompactMode(!compactMode);
  const toggleCriticalAlerts = () => setCriticalAlertsEnabled(!criticalAlertsEnabled);
  const toggleSounds = () => setSoundsEnabled(!soundsEnabled);
  const toggleIpWhitelisting = () => setIpWhitelisting(!ipWhitelisting);
  const toggleLoginNotifications = () => setLoginNotifications(!loginNotifications);
  const toggleBetaFeatures = () => setEnableBetaFeatures(!enableBetaFeatures);
  const toggleTelemetry = () => setTelemetryEnabled(!telemetryEnabled);
  
  // Theme functions
  const handleThemeChange = (newTheme: 'light' | 'dark' | 'system') => {
    setTheme(newTheme);
    // Here you would actually change the theme
  };

  // Save settings to Supabase
  const saveSettings = async () => {
    if (!user?.id) {
      toast.error('Debes estar autenticado para guardar la configuración.');
      return;
    }
    
    setIsLoading(true);
    
    try {
      const userProfile: UserProfile = {
        user_id: user.id,
        name: userName,
        email: userEmail,
        phone: userPhone,
        company: userCompany,
        location: userLocation,
        bio: userBio,
        theme: theme,
        accent_color: accentColor,
        animations_enabled: animationsEnabled,
        reduce_motion: reduceMotion,
        compact_mode: compactMode,
        email_notifications: emailNotifications,
        push_notifications: pushNotifications,
        trading_alerts: tradingAlerts,
        news_updates: newsUpdates,
        critical_alerts_enabled: criticalAlertsEnabled,
        sounds_enabled: soundsEnabled,
        language: language,
        time_format: timeFormat,
        currency: currency,
        date_format: dateFormat,
        timezone: timezone,
        two_factor_enabled: twoFactorEnabled,
        session_timeout: sessionTimeout,
        ip_whitelisting: ipWhitelisting,
        login_notifications: loginNotifications,
      };
      
      await saveUserProfile(userProfile);
      
      setSettingsSaved(true);
      toast.success('¡Configuración guardada con éxito!');
      
      setTimeout(() => setSettingsSaved(false), 3000);
    } catch (error) {
      console.error('Error al guardar la configuración:', error);
      toast.error('No se pudo guardar tu configuración.');
    } finally {
      setIsLoading(false);
    }
  };
  
  const accentColors = [
    { name: 'Violeta', value: 'violet', class: 'bg-violet-500' },
    { name: 'Azul', value: 'blue', class: 'bg-blue-500' },
    { name: 'Verde', value: 'green', class: 'bg-emerald-500' },
    { name: 'Vermelho', value: 'red', class: 'bg-rose-500' },
    { name: 'Âmbar', value: 'amber', class: 'bg-amber-500' },
    { name: 'Indigo', value: 'indigo', class: 'bg-indigo-500' },
  ];

  // Password functions
  const handlePasswordChange = async () => {
    if (!currentPassword || !newPassword || !confirmPassword) {
      setPasswordError('Todos los campos son requeridos');
      return;
    }
    
    if (newPassword.length < 8) {
      setPasswordError('La nueva contraseña debe tener al menos 8 caracteres');
      return;
    }
    
    if (newPassword !== confirmPassword) {
      setPasswordError('Las contraseñas no coinciden');
      return;
    }
    
    setIsLoading(true);
    setPasswordError('');
    
    try {
      const { error } = await supabase.auth.updateUser({
        password: newPassword,
      });
      
      if (error) {
        console.error('Error al cambiar la contraseña:', error);
        setPasswordError(error.message);
      } else {
        setPasswordSuccess(true);
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
        toast.success('¡Contraseña actualizada con éxito!');
        
        setTimeout(() => {
          setPasswordSuccess(false);
        }, 3000);
      }
    } catch (error: any) {
      console.error('Error al cambiar la contraseña:', error);
      setPasswordError('Ocurrió un error al intentar cambiar tu contraseña');
    } finally {
      setIsLoading(false);
    }
  };
  
  // Email change function
  const handleEmailChange = async () => {
    if (!user) return;
    
    setIsLoading(true);
    
    try {
      const { error } = await supabase.auth.updateUser({
        email: newEmail
      });
      
      if (error) {
        throw error;
      }
      
      setUserEmail(newEmail);
      setEmailChangeSuccess(true);
      setNewEmail('');
      
      toast.success('Um email de confirmação foi enviado para o novo endereço.');
      
      setTimeout(() => {
        setEmailChangeSuccess(false);
      }, 3000);
    } catch (error: any) {
      toast.error('Não foi possível atualizar seu email: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };

  // Render the main content based on active tab
  const renderContent = () => {
    switch (activeTab) {
      case 'cuenta':
        return (
          <div className="space-y-8">
            {/* User Profile Section */}
            <div className="border rounded-xl shadow-sm overflow-hidden">
              <div className="p-5 border-b bg-muted/40 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <User className="text-primary" size={18} />
                  <h2 className="text-lg font-semibold">Perfil de Usuario</h2>
                </div>
                <div className="text-xs text-muted-foreground bg-primary/5 px-3 py-1 rounded-full">
                  Plan Pro
                </div>
              </div>
              
              <div className="p-6">
                <div className="flex flex-col md:flex-row items-start gap-8">
                  {/* Profile picture section */}
                  <div className="w-full md:w-auto flex flex-col items-center gap-4">
                    <div className="relative group">
                      <div className="h-32 w-32 rounded-full bg-primary/20 border-4 border-background flex items-center justify-center text-primary overflow-hidden">
                        <User size={64} />
                      </div>
                      <button className="absolute bottom-0 right-0 bg-primary text-white p-2 rounded-full shadow-lg opacity-90 hover:opacity-100 transition-opacity">
                        <Camera size={16} />
                      </button>
                    </div>
                    <button className="text-sm text-primary hover:text-primary/80 flex items-center gap-1.5">
                      <Upload size={14} />
                      Cambiar foto
                    </button>
                  </div>
                  
                  {/* User info fields */}
                  <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <label htmlFor="name" className="block text-sm font-medium">
                        Nombre completo
                      </label>
                      <div className="relative">
                        <input
                          id="name"
                          type="text"
                          value={userName}
                          onChange={(e) => setUserName(e.target.value)}
                          className="w-full p-2.5 bg-background border border-border rounded-md shadow-sm focus:border-primary focus:ring-1 focus:ring-primary pl-9"
                        />
                        <User size={16} className="absolute left-3 top-3 text-muted-foreground" />
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <label htmlFor="email" className="block text-sm font-medium">
                        Correo electrónico
                      </label>
                      <div className="relative">
                        <input
                          id="email"
                          type="email"
                          value={userEmail}
                          onChange={(e) => setUserEmail(e.target.value)}
                          className="w-full p-2.5 bg-background border border-border rounded-md shadow-sm focus:border-primary focus:ring-1 focus:ring-primary pl-9"
                          readOnly
                        />
                        <Mail size={16} className="absolute left-3 top-3 text-muted-foreground" />
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Para cambiar tu correo, usa la sección "Cambiar Correo" más abajo
                      </p>
                    </div>
                    
                    <div className="space-y-2">
                      <label htmlFor="phone" className="block text-sm font-medium">
                        Teléfono
                      </label>
                      <div className="relative">
                        <input
                          id="phone"
                          type="tel"
                          value={userPhone}
                          onChange={(e) => setUserPhone(e.target.value)}
                          className="w-full p-2.5 bg-background border border-border rounded-md shadow-sm focus:border-primary focus:ring-1 focus:ring-primary pl-9"
                        />
                        <Phone size={16} className="absolute left-3 top-3 text-muted-foreground" />
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <label htmlFor="company" className="block text-sm font-medium">
                        Empresa
                      </label>
                      <div className="relative">
                        <input
                          id="company"
                          type="text"
                          value={userCompany}
                          onChange={(e) => setUserCompany(e.target.value)}
                          className="w-full p-2.5 bg-background border border-border rounded-md shadow-sm focus:border-primary focus:ring-1 focus:ring-primary pl-9"
                        />
                        <Building size={16} className="absolute left-3 top-3 text-muted-foreground" />
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <label htmlFor="location" className="block text-sm font-medium">
                        Ubicación
                      </label>
                      <div className="relative">
                        <input
                          id="location"
                          type="text"
                          value={userLocation}
                          onChange={(e) => setUserLocation(e.target.value)}
                          className="w-full p-2.5 bg-background border border-border rounded-md shadow-sm focus:border-primary focus:ring-1 focus:ring-primary pl-9"
                        />
                        <MapPin size={16} className="absolute left-3 top-3 text-muted-foreground" />
                      </div>
                    </div>
                    
                    <div className="col-span-2 space-y-2">
                      <label htmlFor="bio" className="block text-sm font-medium">
                        Biografía
                      </label>
                      <div className="relative">
                        <textarea
                          id="bio"
                          value={userBio}
                          onChange={(e) => setUserBio(e.target.value)}
                          rows={3}
                          className="w-full p-2.5 bg-background border border-border rounded-md shadow-sm focus:border-primary focus:ring-1 focus:ring-primary"
                        />
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Breve descripción sobre ti que se mostrará en tu perfil público.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="p-4 bg-muted/10 border-t flex justify-between items-center">
                <div className="text-sm text-muted-foreground">
                  Última actualización: <span className="font-medium">22/07/2023</span>
                </div>
                <button
                  onClick={saveSettings}
                  className="px-4 py-2 bg-primary hover:bg-primary/90 text-white rounded-md text-sm font-medium flex items-center gap-2 transition-colors"
                >
                  <Save size={14} />
                  Guardar perfil
                </button>
              </div>
            </div>
            
            {/* Change Email Section */}
            <div className="border rounded-xl shadow-sm overflow-hidden">
              <div className="p-5 border-b bg-muted/40 flex items-center gap-2">
                <Mail className="text-primary" size={18} />
                <h2 className="text-lg font-semibold">Cambiar Correo</h2>
              </div>
              
              <div className="p-6">
                <div className="max-w-md">
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <label className="block text-sm font-medium">Correo actual</label>
                      <div className="px-3 py-2 border border-border rounded-md bg-muted/20">
                        <span className="text-sm">{userEmail}</span>
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <label htmlFor="new-email" className="block text-sm font-medium">
                        Nuevo Correo
                      </label>
                      <div className="relative">
                        <input
                          id="new-email"
                          type="email"
                          value={newEmail}
                          onChange={(e) => setNewEmail(e.target.value)}
                          placeholder="tu-nuevo-correo@ejemplo.com"
                          className="w-full p-2.5 bg-background border border-border rounded-md shadow-sm focus:border-primary focus:ring-1 focus:ring-primary pl-9"
                        />
                        <Mail size={16} className="absolute left-3 top-3 text-muted-foreground" />
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Recibirás un enlace de confirmación en el nuevo correo para completar el cambio.
                      </p>
                    </div>
                    
                    {emailChangeSuccess && (
                      <div className="bg-emerald-50 border border-emerald-200 text-emerald-700 px-4 py-2 rounded-md text-sm flex items-center gap-2">
                        <CheckCircle2 size={16} />
                        <p>¡Solicitud de cambio de correo enviada con éxito!</p>
                      </div>
                    )}
                    
                    <button
                      onClick={handleEmailChange}
                      disabled={!newEmail || newEmail === userEmail}
                      className="px-4 py-2 bg-primary hover:bg-primary/90 disabled:bg-muted disabled:text-muted-foreground text-white rounded-md text-sm font-medium transition-colors"
                    >
                      Solicitar cambio de correo
                    </button>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Change Password Section */}
            <div className="border rounded-xl shadow-sm overflow-hidden">
              <div className="p-5 border-b bg-muted/40 flex items-center gap-2">
                <Lock className="text-primary" size={18} />
                <h2 className="text-lg font-semibold">Cambiar Contraseña</h2>
              </div>
              
              <div className="p-6">
                <div className="max-w-md">
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <label htmlFor="current-password" className="block text-sm font-medium">
                        Contraseña Actual
                      </label>
                      <div className="relative">
                        <input
                          id="current-password"
                          type="password"
                          value={currentPassword}
                          onChange={(e) => setCurrentPassword(e.target.value)}
                          className="w-full p-2.5 bg-background border border-border rounded-md shadow-sm focus:border-primary focus:ring-1 focus:ring-primary pl-9"
                        />
                        <Lock size={16} className="absolute left-3 top-3 text-muted-foreground" />
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <label htmlFor="new-password" className="block text-sm font-medium">
                        Nueva Contraseña
                      </label>
                      <div className="relative">
                        <input
                          id="new-password"
                          type="password"
                          value={newPassword}
                          onChange={(e) => setNewPassword(e.target.value)}
                          className="w-full p-2.5 bg-background border border-border rounded-md shadow-sm focus:border-primary focus:ring-1 focus:ring-primary pl-9"
                        />
                        <Lock size={16} className="absolute left-3 top-3 text-muted-foreground" />
                      </div>
                      <p className="text-xs text-muted-foreground">
                        La contraseña debe tener al menos 8 caracteres.
                      </p>
                    </div>
                    
                    <div className="space-y-2">
                      <label htmlFor="confirm-password" className="block text-sm font-medium">
                        Confirmar Nueva Contraseña
                      </label>
                      <div className="relative">
                        <input
                          id="confirm-password"
                          type="password"
                          value={confirmPassword}
                          onChange={(e) => setConfirmPassword(e.target.value)}
                          className="w-full p-2.5 bg-background border border-border rounded-md shadow-sm focus:border-primary focus:ring-1 focus:ring-primary pl-9"
                        />
                        <Lock size={16} className="absolute left-3 top-3 text-muted-foreground" />
                      </div>
                    </div>
                    
                    {passwordError && (
                      <div className="bg-rose-50 border border-rose-200 text-rose-700 px-4 py-2 rounded-md text-sm">
                        {passwordError}
                      </div>
                    )}
                    
                    {passwordSuccess && (
                      <div className="bg-emerald-50 border border-emerald-200 text-emerald-700 px-4 py-2 rounded-md text-sm flex items-center gap-2">
                        <CheckCircle2 size={16} />
                        <p>¡Contraseña cambiada con éxito!</p>
                      </div>
                    )}
                    
                    <button
                      onClick={handlePasswordChange}
                      disabled={!currentPassword || !newPassword || !confirmPassword}
                      className="px-4 py-2 bg-primary hover:bg-primary/90 disabled:bg-muted disabled:text-muted-foreground text-white rounded-md text-sm font-medium transition-colors"
                    >
                      Cambiar contraseña
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );
        
      case 'seguridad':
        return (
          <div className="space-y-8">
            {/* Security settings */}
            <div className="border rounded-xl shadow-sm overflow-hidden">
              <div className="p-5 border-b bg-muted/40 flex items-center gap-2">
                <Shield className="text-primary" size={18} />
                <h2 className="text-lg font-semibold">Seguridad</h2>
              </div>
              
              <div className="p-6 space-y-4">
                <div className="bg-amber-50 border border-amber-200 text-amber-800 p-4 rounded-lg flex gap-3">
                  <Info size={18} className="text-amber-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium">Tu privacidad es importante</h4>
                    <p className="text-sm mt-1">
                      Conoce cómo tratamos tus datos en nuestra <a href="#" className="text-primary font-medium hover:underline">Política de Privacidad</a>.
                    </p>
                  </div>
                </div>
                
                <div className="p-4 rounded-lg border border-border">
                  <div className="flex justify-between items-center mb-4">
                    <h4 className="font-medium">Mis Datos</h4>
                    <button className="text-xs text-primary hover:text-primary/80 flex items-center gap-1.5">
                      <Download size={12} /> Descargar mis datos
                    </button>
                  </div>
                  
                  <div className="text-sm text-muted-foreground">
                    <p>Puedes solicitar una copia de tus datos o solicitar la eliminación de tu cuenta en cualquier momento.</p>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Two-factor authentication */}
            <div className="border rounded-xl shadow-sm overflow-hidden">
              <div className="p-5 border-b bg-muted/40 flex items-center gap-2">
                <Lock className="text-primary" size={18} />
                <h2 className="text-lg font-semibold">Autenticación de Dos Factores</h2>
              </div>
              
              <div className="p-6 space-y-4">
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="font-medium">Autenticación de Dos Factores</h3>
                    <p className="text-sm text-muted-foreground">Seguridad adicional para proteger tu cuenta</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" checked={twoFactorEnabled} onChange={toggleTwoFactor} className="sr-only peer" />
                    <div className="w-11 h-6 bg-muted rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                  </label>
                </div>
                
                <div className="mt-6">
                  <label htmlFor="session-timeout" className="block text-sm font-medium mb-2">
                    Tiempo de sesión
                  </label>
                  <input 
                    type="number" 
                    id="session-timeout"
                    className="w-full p-2.5 bg-background border border-border rounded-md shadow-sm focus:border-primary focus:ring-1 focus:ring-primary"
                    value={sessionTimeout}
                    onChange={(e) => setSessionTimeout(Number(e.target.value))}
                  />
                  <p className="text-xs text-muted-foreground mt-2">
                    Define el tiempo máximo de inactividad antes de que se requiera una nueva autenticación (en minutos).
                  </p>
                </div>
              </div>
            </div>
          </div>
        );
        
      default:
        return (
          <div className="p-8 text-center">
            <h3 className="text-lg font-medium mb-2">Selecciona una categoría</h3>
            <p className="text-muted-foreground">Elige una categoría de configuración en el menú lateral para comenzar.</p>
          </div>
        );
    }
  };

  return (
    <div className="container max-w-7xl mx-auto py-8 px-4 animate-in fade-in duration-500">
      {/* Header with notification for saved settings */}
      <div className="relative mb-8">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold mb-2 flex items-center gap-2">
              <Settings className="text-primary" size={28} />
              Configuración
            </h1>
            <p className="text-muted-foreground">Personaliza tu experiencia en Million Bots</p>
          </div>
          
          <button
            onClick={saveSettings}
            disabled={isLoading}
            className="mt-4 md:mt-0 px-4 py-2 bg-primary hover:bg-primary/90 text-white rounded-md flex items-center gap-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <span className="animate-spin h-4 w-4 border-2 border-current border-t-transparent rounded-full"></span>
                <span>Guardando...</span>
              </>
            ) : (
              <>
                <Save size={16} />
                <span>Guardar Cambios</span>
              </>
            )}
          </button>
        </div>
        
        {/* Notification when settings are saved */}
        {settingsSaved && (
          <div className="fixed top-6 right-6 z-50 animate-in slide-in-from-top-2 fade-in duration-300">
            <div className="bg-emerald-500 text-white px-4 py-3 rounded-lg shadow-md flex items-center gap-2">
              <CheckCircle2 size={18} />
              <span>¡Configuración guardada con éxito!</span>
            </div>
          </div>
        )}

        {/* Settings navigation tabs */}
        <div className="border-b border-border mb-8">
          <div className="flex flex-wrap gap-0">
            <button 
              onClick={() => setActiveTab('cuenta')} 
              className={cn(
                "px-5 py-3 font-medium transition-colors border-b-2 -mb-px",
                activeTab === 'cuenta' 
                  ? "border-primary text-primary" 
                  : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
              )}
            >
              Perfil
            </button>
            <button 
              onClick={() => setActiveTab('seguridad')} 
              className={cn(
                "px-5 py-3 font-medium transition-colors border-b-2 -mb-px",
                activeTab === 'seguridad' 
                  ? "border-primary text-primary" 
                  : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
              )}
            >
              Seguridad
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
        {/* Sidebar navigation */}
        <div className="md:col-span-1 space-y-6">
          <div className="border rounded-xl shadow-sm overflow-hidden">
            <div className="p-4 border-b bg-muted/40">
              <h2 className="text-lg font-semibold">Categorías</h2>
            </div>
            <div className="p-1.5">
              <button 
                onClick={() => setActiveTab('cuenta')}
                className={cn(
                  "w-full flex items-center gap-3 p-3 rounded-md transition-colors",
                  activeTab === 'cuenta' 
                    ? "bg-primary/10 text-primary font-medium" 
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                <User size={18} />
                <span>Perfil</span>
              </button>
              <button 
                onClick={() => setActiveTab('seguridad')}
                className={cn(
                  "w-full flex items-center gap-3 p-3 rounded-md transition-colors",
                  activeTab === 'seguridad' 
                    ? "bg-primary/10 text-primary font-medium" 
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                <Shield size={18} />
                <span>Seguridad</span>
              </button>
            </div>
          </div>

          {/* User profile summary card */}
          <div className="border rounded-xl overflow-hidden">
            <div className="bg-gradient-to-br from-primary/20 to-primary/5 p-6 flex flex-col items-center text-center">
              <div className="h-20 w-20 rounded-full bg-primary/20 border-4 border-background flex items-center justify-center text-primary mb-3">
                <User size={32} />
              </div>
              <h3 className="font-medium">{userName || user?.email}</h3>
              <p className="text-sm text-muted-foreground">{userEmail || user?.email}</p>
              <div className="mt-2 inline-flex items-center text-xs text-primary bg-primary/10 px-2 py-1 rounded-full">
                Plan Pro
              </div>
            </div>
            <div className="p-3 bg-muted/20">
              <button 
                onClick={() => setActiveTab('cuenta')}
                className="w-full text-sm text-center text-primary hover:text-primary/80"
              >
                Editar perfil
              </button>
            </div>
          </div>

          {/* Quick help card */}
          <div className="border rounded-xl p-4 bg-muted/10">
            <div className="flex items-start gap-3">
              <HelpCircle className="text-primary mt-0.5" size={18} />
              <div>
                <h3 className="font-medium mb-1">Ayuda y Soporte</h3>
                <p className="text-sm text-muted-foreground mb-3">
                  ¿Necesitas ayuda con tu configuración? Nuestro equipo de soporte está disponible para ayudarte.
                </p>
                <a href="#" className="text-sm text-primary hover:underline">
                  Contáctanos
                </a>
              </div>
            </div>
          </div>
        </div>

        {/* Main settings content */}
        <div className="md:col-span-3">
          {isLoading ? (
            <div className="flex items-center justify-center py-20">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            </div>
          ) : (
            renderContent()
          )}
        </div>
      </div>
      
      {/* Footer */}
      <div className="mt-16 pt-8 border-t border-border flex justify-between items-center text-sm text-muted-foreground">
        <div>
          <p>© 2023 Million Bots. Todos los derechos reservados.</p>
        </div>
        <div className="flex gap-6">
          <a href="#" className="hover:text-primary transition-colors">Términos</a>
          <a href="#" className="hover:text-primary transition-colors">Privacidad</a>
          <a href="#" className="hover:text-primary transition-colors">Contacto</a>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
