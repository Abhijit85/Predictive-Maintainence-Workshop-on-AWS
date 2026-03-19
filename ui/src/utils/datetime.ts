/**
 * Parse a backend datetime string as UTC.
 *
 * The backend writes timestamps as "YYYY-MM-DD HH:MM:SS" using
 * datetime.now() on a UTC server. Browsers parse this space-separated
 * format as **local time**, not UTC, which causes incorrect time diffs
 * and display for users in non-UTC timezones.
 *
 * Converting to ISO 8601 ("YYYY-MM-DDTHH:MM:SSZ") forces correct UTC
 * interpretation everywhere.
 */
export const parseUTCDatetime = (dt: string): Date =>
  new Date(dt.includes('T') || dt.includes('Z') ? dt : dt.replace(' ', 'T') + 'Z');
