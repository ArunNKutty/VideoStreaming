declare module 'hls.js' {
  export interface HlsConfig {
    enableWorker?: boolean;
    lowLatencyMode?: boolean;
    backBufferLength?: number;
    [key: string]: any;
  }

  export interface Level {
    bitrate: number;
    width?: number;
    height?: number;
    name?: string;
    [key: string]: any;
  }

  export interface ErrorData {
    type: string;
    details: string;
    fatal: boolean;
    [key: string]: any;
  }

  export default class Hls {
    static isSupported(): boolean;
    static Events: {
      MANIFEST_PARSED: string;
      ERROR: string;
      LEVEL_SWITCHED: string;
      [key: string]: string;
    };
    static ErrorTypes: {
      NETWORK_ERROR: string;
      MEDIA_ERROR: string;
      [key: string]: string;
    };

    levels: Level[];

    constructor(config?: HlsConfig);
    loadSource(url: string): void;
    attachMedia(media: HTMLMediaElement): void;
    on(event: string, callback: (event: string, data: any) => void): void;
    destroy(): void;
    recoverMediaError(): void;
  }
}
