// Type declaration for Umami analytics
interface Window {
  umami?: {
    track: (eventName: string, eventData?: Record<string, any>) => void;
  };
}
