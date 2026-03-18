import { VoiceJoinRequestSummary, WorkspaceMessage } from './workspace.models';

export interface AppEventsReadyEvent {
  type: 'ready';
  user_id: string;
}

export interface AppEventsPongEvent {
  type: 'pong';
}

export interface AppEventsErrorEvent {
  type: 'error';
  detail: string;
}

export interface AppPresenceUpdatedEvent {
  type: 'presence_updated';
  user_id: string;
  is_online: boolean;
  last_active_at: string;
}

export interface AppMessageCreatedEvent {
  type: 'message_created';
  server_id: string;
  message: WorkspaceMessage;
}

export interface AppServersChangedEvent {
  type: 'servers_changed';
  reason: string;
}

export interface AppServerChangedEvent {
  type: 'server_changed';
  server_id: string;
  reason: string;
}

export interface AppVoiceInboxChangedEvent {
  type: 'voice_inbox_changed';
}

export interface AppVoiceRequestResolvedEvent {
  type: 'voice_request_resolved';
  request: VoiceJoinRequestSummary;
}

export type AppEventsMessage =
  | AppEventsReadyEvent
  | AppEventsPongEvent
  | AppEventsErrorEvent
  | AppPresenceUpdatedEvent
  | AppMessageCreatedEvent
  | AppServersChangedEvent
  | AppServerChangedEvent
  | AppVoiceInboxChangedEvent
  | AppVoiceRequestResolvedEvent;
