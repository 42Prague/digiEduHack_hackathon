import { AccessLevel } from './access-level';

export interface User {
	id: string;
	name: string;
	surname: string;
	email: string;
	accessLevel: AccessLevel;
	regionId?: string;
	schoolId?: string;
}

