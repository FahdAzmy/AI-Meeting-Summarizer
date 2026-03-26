import { detectPlatform, isValidMeetingUrl } from '../../src/lib/utils';

describe('URL Platform Verification', () => {
  it('should detect Google Meet URLs', () => {
    expect(detectPlatform('https://meet.google.com/abc-defg-hij')).toBe('google_meet');
  });

  it('should detect Zoom URLs', () => {
    expect(detectPlatform('https://zoom.us/j/123456789')).toBe('zoom');
    expect(detectPlatform('https://company.zoom.us/j/123456789')).toBe('zoom');
  });

  it('should detect MS Teams URLs', () => {
    expect(detectPlatform('https://teams.microsoft.com/l/meetup-join/19%3ameeting_xyz')).toBe('teams');
  });

  it('should gracefully fallback to unknown on invalid urls', () => {
    expect(detectPlatform('https://example.com/not-a-meeting')).toBeNull();
  });
});

describe('isValidMeetingUrl', () => {
  it('should validate proper meeting URLs', () => {
    expect(isValidMeetingUrl('https://meet.google.com/abc-defg-hij')).toBe(true);
  });

  it('should reject invalid URLs', () => {
    expect(isValidMeetingUrl('not-a-url')).toBe(false);
    expect(isValidMeetingUrl('https://example.com')).toBe(false);
  });
});
