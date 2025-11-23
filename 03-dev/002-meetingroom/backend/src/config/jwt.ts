export const jwtConfig = {
  secret: process.env['JWT_ACCESS_SECRET'] || 'your-access-secret-key',
  refreshSecret: process.env['JWT_REFRESH_SECRET'] || 'your-refresh-secret-key',
  issuer: 'yds-meeting-system',
  audience: 'yds-clients'
};