import { HttpErrorResponse } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { Component, DestroyRef, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';

import { AuthSessionResponse } from './core/models/auth.models';
import { ApiHealthResponse } from './core/models/system.models';
import { CurrentUserResponse, WorkspaceChannel, WorkspaceServer } from './core/models/workspace.models';
import { AuthApiService } from './core/api/auth-api.service';
import { SystemApiService } from './core/api/system-api.service';
import { WorkspaceApiService } from './core/api/workspace-api.service';
import { VoiceParticipant, VoiceRoomService } from './core/services/voice-room.service';

type AuthMode = 'login' | 'register';
type ChannelKind = 'text' | 'voice';

interface LoginFormModel {
  login: string;
  password: string;
}

interface RegisterFormModel {
  login: string;
  password: string;
  full_name: string;
  nick: string;
  character_name: string;
}

interface CreateGroupFormModel {
  name: string;
  description: string;
}

interface CreateChannelFormModel {
  name: string;
  topic: string;
  type: ChannelKind;
}

interface ServerShortcut {
  id: string;
  label: string;
  name: string;
  active: boolean;
}

interface MemberCard {
  name: string;
  role: string;
  status: 'online' | 'idle' | 'focus';
}

const ADMIN_CREDENTIALS: LoginFormModel = {
  login: 'weren9000',
  password: 'Vfrfhjys9000'
};

const SESSION_STORAGE_KEY = 'tescord.session';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent {
  private readonly systemApi = inject(SystemApiService);
  private readonly authApi = inject(AuthApiService);
  private readonly workspaceApi = inject(WorkspaceApiService);
  private readonly voiceRoom = inject(VoiceRoomService);
  private readonly destroyRef = inject(DestroyRef);

  readonly health = signal<ApiHealthResponse | null>(null);
  readonly healthError = signal<string | null>(null);
  readonly authError = signal<string | null>(null);
  readonly workspaceError = signal<string | null>(null);
  readonly managementError = signal<string | null>(null);
  readonly managementSuccess = signal<string | null>(null);
  readonly authLoading = signal(false);
  readonly workspaceLoading = signal(false);
  readonly createGroupLoading = signal(false);
  readonly createChannelLoading = signal(false);
  readonly authMode = signal<AuthMode>('login');

  readonly session = signal<AuthSessionResponse | null>(null);
  readonly currentUser = signal<CurrentUserResponse | null>(null);
  readonly servers = signal<WorkspaceServer[]>([]);
  readonly channels = signal<WorkspaceChannel[]>([]);
  readonly selectedServerId = signal<string | null>(null);
  readonly selectedChannelId = signal<string | null>(null);

  readonly loginForm: LoginFormModel = {
    login: '',
    password: ''
  };

  readonly registerForm: RegisterFormModel = {
    login: '',
    password: '',
    full_name: '',
    nick: '',
    character_name: ''
  };

  readonly createGroupForm: CreateGroupFormModel = {
    name: '',
    description: ''
  };

  readonly createChannelForm: CreateChannelFormModel = {
    name: '',
    topic: '',
    type: 'text'
  };

  readonly isAuthenticated = computed(() => this.session() !== null);
  readonly isAdmin = computed(() => this.currentUser()?.is_admin === true);
  readonly voiceParticipants = this.voiceRoom.participants;
  readonly voiceError = this.voiceRoom.error;
  readonly voiceState = this.voiceRoom.state;
  readonly voiceMuted = this.voiceRoom.localMuted;

  readonly activeServer = computed(() => {
    const serverId = this.selectedServerId();
    return this.servers().find((server) => server.id === serverId) ?? null;
  });

  readonly activeChannel = computed(() => {
    const channelId = this.selectedChannelId();
    return this.channels().find((channel) => channel.id === channelId) ?? null;
  });
  readonly textChannels = computed(() => this.channels().filter((channel) => channel.type === 'text'));
  readonly voiceChannels = computed(() => this.channels().filter((channel) => channel.type === 'voice'));

  readonly connectedVoiceChannel = computed(() => {
    const connectedChannelId = this.voiceRoom.activeChannelId();
    return this.channels().find((channel) => channel.id === connectedChannelId) ?? null;
  });

  readonly isVoiceChannelSelected = computed(() => this.activeChannel()?.type === 'voice');
  readonly hasVoiceConnection = computed(() => this.voiceRoom.isConnected() && this.connectedVoiceChannel() !== null);
  readonly isInActiveVoiceChannel = computed(
    () => this.hasVoiceConnection() && this.activeChannel()?.id === this.connectedVoiceChannel()?.id
  );
  readonly showVoiceDock = computed(() => this.hasVoiceConnection() && !this.isInActiveVoiceChannel());

  readonly canManageActiveGroup = computed(() => {
    const activeServer = this.activeServer();
    const currentUser = this.currentUser();
    if (!activeServer || !currentUser) {
      return false;
    }

    return currentUser.is_admin || activeServer.member_role === 'owner' || activeServer.member_role === 'admin';
  });

  readonly statusTone = computed(() => {
    if (
      this.authError() ||
      this.workspaceError() ||
      this.healthError() ||
      this.managementError() ||
      this.voiceError()
    ) {
      return 'offline';
    }

    if (
      this.authLoading() ||
      this.workspaceLoading() ||
      this.createGroupLoading() ||
      this.createChannelLoading() ||
      this.voiceState() === 'connecting'
    ) {
      return 'checking';
    }

    const health = this.health();
    if (!health) {
      return 'checking';
    }

    return health.status === 'ok' && health.database === 'online' ? 'healthy' : 'warning';
  });

  readonly statusLabel = computed(() => {
    if (this.voiceError()) {
      return 'Ошибка голосового канала';
    }

    if (this.managementError()) {
      return 'Ошибка управления группой';
    }

    if (this.authError()) {
      return 'Нужна авторизация';
    }

    if (this.workspaceError()) {
      return 'Не удалось загрузить рабочее пространство';
    }

    if (this.healthError()) {
      return 'Бэкенд недоступен';
    }

    if (this.voiceState() === 'connecting') {
      return 'Подключаем голосовой канал';
    }

    if (this.hasVoiceConnection()) {
      return `В голосе: ${this.connectedVoiceChannel()?.name ?? 'канал активен'}`;
    }

    if (this.createGroupLoading()) {
      return 'Создаем новую группу';
    }

    if (this.createChannelLoading()) {
      return 'Создаем новый канал';
    }

    if (this.authLoading()) {
      return this.authMode() === 'register' ? 'Создаем аккаунт' : 'Выполняем вход';
    }

    if (this.workspaceLoading()) {
      return 'Загружаем группы и каналы';
    }

    const health = this.health();
    if (!health) {
      return 'Проверяем API';
    }

    return health.status === 'ok' && health.database === 'online'
      ? 'API и база данных готовы'
      : 'API доступно, база данных еще поднимается';
  });

  readonly activeChannelHeading = computed(() => {
    const channel = this.activeChannel();
    if (!channel) {
      return 'Канал не выбран';
    }

    return channel.type === 'voice' ? `Голосовой: ${channel.name}` : `# ${channel.name}`;
  });

  readonly voiceStatusLabel = computed(() => {
    if (this.voiceError()) {
      return this.voiceError();
    }

    if (this.voiceState() === 'connecting') {
      return 'Подключаемся к голосовой комнате';
    }

    if (this.isInActiveVoiceChannel()) {
      return this.voiceMuted()
        ? 'Вы в канале, микрофон выключен'
        : 'Вы в канале, микрофон включен';
    }

    if (this.hasVoiceConnection()) {
      return `Сейчас активен канал ${this.connectedVoiceChannel()?.name ?? ''}`.trim();
    }

    return 'Можно подключиться к голосовому каналу';
  });

  readonly voiceDockLabel = computed(() => {
    if (!this.hasVoiceConnection()) {
      return '';
    }

    return this.voiceMuted()
      ? 'Голосовой канал работает в фоне, микрофон выключен'
      : 'Голосовой канал работает в фоне, микрофон включен';
  });

  readonly composerHint = computed(() => {
    if (this.showVoiceDock()) {
      return `Вы остаетесь в голосовом канале ${this.connectedVoiceChannel()?.name ?? ''}, пока не выйдете из него или не переключитесь в другую группу.`;
    }

    if (this.isVoiceChannelSelected()) {
      return 'Голосовой канал использует микрофон браузера и держится активным, пока вы находитесь в этой группе.';
    }

    return 'Следующим шагом здесь появятся история сообщений, отправка текста и вложения.';
  });

  readonly serverShortcuts = computed<ServerShortcut[]>(() =>
    this.servers().map((server) => ({
      id: server.id,
      label: server.name.slice(0, 2).toUpperCase(),
      name: server.name,
      active: server.id === this.selectedServerId()
    }))
  );

  readonly memberCards = computed<MemberCard[]>(() => {
    const user = this.currentUser();
    const baseCards: MemberCard[] = [
      { name: 'Tescord Bot', role: 'Система', status: 'online' },
      { name: 'WebRTC', role: 'Голосовые каналы', status: 'focus' },
      { name: 'Attachments', role: 'Следующий этап', status: 'idle' }
    ];

    if (!user) {
      return baseCards;
    }

    return [
      {
        name: user.nick,
        role: user.is_admin ? 'Администратор' : user.character_name ?? 'Игрок в сети',
        status: 'online'
      },
      ...baseCards
    ];
  });

  readonly localizedEnvironment = computed(() => {
    const environment = this.health()?.environment;

    if (environment === 'development') {
      return 'разработка';
    }

    if (environment === 'staging') {
      return 'стейджинг';
    }

    if (environment === 'production') {
      return 'прод';
    }

    if (environment === 'test') {
      return 'тест';
    }

    return environment ?? 'неизвестно';
  });

  readonly localizedDatabaseStatus = computed(() => {
    const database = this.health()?.database;

    if (database === 'online') {
      return 'онлайн';
    }

    if (database === 'offline') {
      return 'офлайн';
    }

    return 'неизвестно';
  });

  constructor() {
    this.loadHealth();
    this.restoreSession();
  }

  switchAuthMode(mode: AuthMode): void {
    this.authMode.set(mode);
    this.authError.set(null);
  }

  useAdminAccount(): void {
    this.authMode.set('login');
    this.loginForm.login = ADMIN_CREDENTIALS.login;
    this.loginForm.password = ADMIN_CREDENTIALS.password;
    this.authError.set(null);
  }

  submitLogin(): void {
    const payload = {
      login: this.loginForm.login.trim(),
      password: this.loginForm.password
    };

    if (!payload.login || !payload.password) {
      this.authError.set('Введите логин и пароль');
      return;
    }

    this.authLoading.set(true);
    this.authError.set(null);

    this.authApi
      .login(payload)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (session) => this.handleAuthenticatedSession(session),
        error: (error) => {
          this.authLoading.set(false);
          this.authError.set(this.extractErrorMessage(error, 'Не удалось выполнить вход'));
        }
      });
  }

  submitRegistration(): void {
    const payload = {
      login: this.registerForm.login.trim(),
      password: this.registerForm.password,
      full_name: this.registerForm.full_name.trim(),
      nick: this.registerForm.nick.trim(),
      character_name: this.registerForm.character_name.trim()
    };

    if (!payload.login || !payload.password || !payload.full_name || !payload.nick || !payload.character_name) {
      this.authError.set('Заполните все поля регистрации');
      return;
    }

    this.authLoading.set(true);
    this.authError.set(null);

    this.authApi
      .register(payload)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (session) => this.handleAuthenticatedSession(session),
        error: (error) => {
          this.authLoading.set(false);
          this.authError.set(this.extractErrorMessage(error, 'Не удалось зарегистрироваться'));
        }
      });
  }

  submitCreateGroup(): void {
    const token = this.session()?.access_token;
    if (!token) {
      return;
    }

    const payload = {
      name: this.createGroupForm.name.trim(),
      description: this.createGroupForm.description.trim() || null
    };

    if (!payload.name) {
      this.managementError.set('Введите название группы');
      return;
    }

    this.createGroupLoading.set(true);
    this.managementError.set(null);
    this.managementSuccess.set(null);

    this.workspaceApi
      .createServer(token, payload)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (server) => {
          const updatedServers = [...this.servers(), server].sort((left, right) => left.name.localeCompare(right.name, 'ru'));
          this.servers.set(updatedServers);
          this.createGroupForm.name = '';
          this.createGroupForm.description = '';
          this.managementSuccess.set(`Группа «${server.name}» создана`);
          this.createGroupLoading.set(false);
          this.selectServer(server.id);
        },
        error: (error) => {
          this.createGroupLoading.set(false);
          this.managementError.set(this.extractErrorMessage(error, 'Не удалось создать группу'));
        }
      });
  }

  submitCreateChannel(): void {
    const token = this.session()?.access_token;
    const activeServer = this.activeServer();
    if (!token || !activeServer) {
      return;
    }

    const payload = {
      name: this.createChannelForm.name.trim(),
      topic: this.createChannelForm.topic.trim() || null,
      type: this.createChannelForm.type
    };

    if (!payload.name) {
      this.managementError.set('Введите название канала');
      return;
    }

    this.createChannelLoading.set(true);
    this.managementError.set(null);
    this.managementSuccess.set(null);

    this.workspaceApi
      .createChannel(token, activeServer.id, payload)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (channel) => {
          const updatedChannels = [...this.channels(), channel].sort((left, right) => left.position - right.position);
          this.channels.set(updatedChannels);
          this.selectedChannelId.set(channel.id);
          this.createChannelForm.name = '';
          this.createChannelForm.topic = '';
          this.createChannelForm.type = 'text';
          this.managementSuccess.set(
            channel.type === 'voice'
              ? `Голосовой канал ${channel.name} создан`
              : `Текстовый канал #${channel.name} создан`
          );
          this.createChannelLoading.set(false);
        },
        error: (error) => {
          this.createChannelLoading.set(false);
          this.managementError.set(this.extractErrorMessage(error, 'Не удалось создать канал'));
        }
      });
  }

  async joinActiveVoiceChannel(): Promise<void> {
    const activeChannel = this.activeChannel();
    if (!activeChannel || activeChannel.type !== 'voice') {
      return;
    }

    await this.connectToVoiceChannel(activeChannel);
  }

  leaveVoiceChannel(): void {
    this.voiceRoom.leave();
  }

  toggleVoiceMute(): void {
    this.voiceRoom.toggleMute();
  }

  openConnectedVoiceChannel(): void {
    const connectedVoiceChannel = this.connectedVoiceChannel();
    if (!connectedVoiceChannel) {
      return;
    }

    this.selectedChannelId.set(connectedVoiceChannel.id);
  }

  logout(): void {
    this.voiceRoom.leave();
    this.session.set(null);
    this.currentUser.set(null);
    this.servers.set([]);
    this.channels.set([]);
    this.selectedServerId.set(null);
    this.selectedChannelId.set(null);
    this.authError.set(null);
    this.workspaceError.set(null);
    this.managementError.set(null);
    this.managementSuccess.set(null);
    this.authLoading.set(false);
    this.workspaceLoading.set(false);
    this.createGroupLoading.set(false);
    this.createChannelLoading.set(false);
    this.authMode.set('login');
    this.clearStoredSession();
  }

  selectServer(serverId: string): void {
    const token = this.session()?.access_token;
    if (!token) {
      return;
    }

    if (serverId === this.selectedServerId()) {
      return;
    }

    this.voiceRoom.leave();
    this.loadChannels(token, serverId);
  }

  async selectChannel(channel: WorkspaceChannel): Promise<void> {
    this.selectedChannelId.set(channel.id);
    this.workspaceError.set(null);

    if (channel.type === 'voice') {
      await this.connectToVoiceChannel(channel);
    }
  }

  private loadHealth(): void {
    this.systemApi
      .getHealth()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (health) => {
          this.health.set(health);
          this.healthError.set(null);
        },
        error: () => {
          this.health.set(null);
          this.healthError.set('FastAPI не отвечает по адресу http://127.0.0.1:8000/api/health');
        }
      });
  }

  private restoreSession(): void {
    if (typeof localStorage === 'undefined') {
      return;
    }

    const rawSession = localStorage.getItem(SESSION_STORAGE_KEY);
    if (!rawSession) {
      return;
    }

    try {
      const session = JSON.parse(rawSession) as AuthSessionResponse;

      if (!session.access_token || !session.user) {
        throw new Error('Invalid session');
      }

      this.session.set(session);
      this.currentUser.set(session.user);
      this.bootstrapWorkspace(session.access_token);
    } catch {
      this.clearStoredSession();
    }
  }

  private handleAuthenticatedSession(session: AuthSessionResponse): void {
    this.session.set(session);
    this.currentUser.set(session.user);
    this.persistSession(session);
    this.authLoading.set(false);
    this.authError.set(null);
    this.managementError.set(null);
    this.managementSuccess.set(null);
    this.bootstrapWorkspace(session.access_token);
  }

  private bootstrapWorkspace(token: string): void {
    this.workspaceLoading.set(true);
    this.workspaceError.set(null);
    this.voiceRoom.leave();

    forkJoin({
      me: this.workspaceApi.getCurrentUser(token),
      servers: this.workspaceApi.getServers(token)
    })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: ({ me, servers }) => {
          this.currentUser.set(me);
          this.servers.set(servers);

          if (!servers.length) {
            this.selectedServerId.set(null);
            this.selectedChannelId.set(null);
            this.channels.set([]);
            this.workspaceLoading.set(false);
            return;
          }

          const selectedServerId = this.selectedServerId();
          const preferredServerId =
            selectedServerId && servers.some((server) => server.id === selectedServerId)
              ? selectedServerId
              : servers[0].id;

          this.loadChannels(token, preferredServerId);
        },
        error: (error) => {
          this.workspaceLoading.set(false);
          this.voiceRoom.leave();
          this.session.set(null);
          this.currentUser.set(null);
          this.servers.set([]);
          this.channels.set([]);
          this.selectedServerId.set(null);
          this.selectedChannelId.set(null);
          this.clearStoredSession();
          this.authError.set(this.extractErrorMessage(error, 'Сессия устарела. Войдите снова.'));
        }
      });
  }

  private loadChannels(token: string, serverId: string): void {
    const previousSelectedChannelId = this.selectedChannelId();

    this.workspaceLoading.set(true);
    this.workspaceError.set(null);
    this.managementError.set(null);
    this.selectedServerId.set(serverId);
    this.selectedChannelId.set(null);

    this.workspaceApi
      .getChannels(token, serverId)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (channels) => {
          this.channels.set(channels);

          const nextSelectedChannelId =
            (previousSelectedChannelId && channels.some((channel) => channel.id === previousSelectedChannelId)
              ? previousSelectedChannelId
              : null)
            ?? (this.voiceRoom.activeChannelId() && channels.some((channel) => channel.id === this.voiceRoom.activeChannelId())
              ? this.voiceRoom.activeChannelId()
              : null)
            ?? channels[0]?.id
            ?? null;

          this.selectedChannelId.set(nextSelectedChannelId);
          this.workspaceLoading.set(false);
        },
        error: (error) => {
          this.channels.set([]);
          this.workspaceLoading.set(false);
          this.workspaceError.set(this.extractErrorMessage(error, 'Не удалось загрузить каналы выбранной группы'));
        }
      });
  }

  private persistSession(session: AuthSessionResponse): void {
    if (typeof localStorage === 'undefined') {
      return;
    }

    localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
  }

  private clearStoredSession(): void {
    if (typeof localStorage === 'undefined') {
      return;
    }

    localStorage.removeItem(SESSION_STORAGE_KEY);
  }

  private extractErrorMessage(error: unknown, fallback: string): string {
    if (error instanceof HttpErrorResponse) {
      const detail =
        typeof error.error === 'object' && error.error !== null
          ? (error.error as { detail?: unknown }).detail
          : null;

      if (typeof detail === 'string' && detail.trim()) {
        return detail;
      }
    }

    return fallback;
  }

  readonly connectedVoiceChannelId = computed(() => this.connectedVoiceChannel()?.id ?? null);

  voiceParticipantsForChannel(channelId: string): VoiceParticipant[] {
    return this.connectedVoiceChannelId() === channelId ? this.voiceParticipants() : [];
  }

  voiceParticipantTone(participant: VoiceParticipant): 'speaking' | 'open' | 'muted' {
    if (participant.muted) {
      return 'muted';
    }

    return participant.speaking ? 'speaking' : 'open';
  }

  private async connectToVoiceChannel(channel: WorkspaceChannel): Promise<void> {
    const token = this.session()?.access_token;
    const currentUser = this.currentUser();
    if (!token || !currentUser || channel.type !== 'voice') {
      return;
    }

    this.workspaceError.set(null);
    await this.voiceRoom.join(channel.id, token, currentUser);
  }
}
