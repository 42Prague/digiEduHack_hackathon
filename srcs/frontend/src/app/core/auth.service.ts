import { Injectable, signal } from '@angular/core';
import { Router } from '@angular/router';
import { User } from '../models/user';
import { AccessLevel } from '../models/access-level';

@Injectable({ providedIn: 'root' })
export class AuthService {
	// #region Private Properties
	private readonly storageKey: string = 'digi-auth-user';
	private readonly viewAsKey: string = 'digi-auth-viewas';
	private readonly currentUserSignal = signal<User | null>(this.readStoredUser());
	private readonly viewAsSignal = signal<{ level: AccessLevel; regionId?: string; schoolId?: string } | null>(this.readStoredViewAs());
	// #endregion

	// #region Public Methods
	public constructor(private router: Router) {}

	public isLoggedIn(): boolean {
		return !!this.currentUserSignal();
	}

	public currentUser(): User | null {
		const base = this.currentUserSignal();
		const viewAs = this.viewAsSignal();
		if (!base) return null;
		if (!viewAs) return base;
		return {
			...base,
			accessLevel: viewAs.level,
			regionId: viewAs.regionId,
			schoolId: viewAs.schoolId
		};
	}

	public login(params: { id?: string; email: string; name: string; surname: string; accessLevel: AccessLevel; regionId?: string; schoolId?: string }): void {
		const user: User = {
			id: params.id ?? crypto.randomUUID(),
			email: params.email,
			name: params.name,
			surname: params.surname,
			accessLevel: params.accessLevel,
			regionId: params.regionId,
			schoolId: params.schoolId
		};
		localStorage.setItem(this.storageKey, JSON.stringify(user));
		this.currentUserSignal.set(user);
		this.clearViewAs();
		void this.router.navigateByUrl('/');
	}

	public logout(): void {
		localStorage.removeItem(this.storageKey);
		this.clearViewAs();
		this.currentUserSignal.set(null);
		void this.router.navigateByUrl('/login');
	}

	public isViewAs(): boolean {
		return !!this.viewAsSignal();
	}

	public viewAsInfo(): { level: AccessLevel; regionId?: string; schoolId?: string } | null {
		return this.viewAsSignal();
	}

	public enterViewAsRegion(regionId: string): void {
		this.setViewAs({ level: AccessLevel.Region, regionId });
	}

	public enterViewAsSchool(schoolId: string): void {
		this.setViewAs({ level: AccessLevel.School, schoolId });
	}

	public exitViewAs(): void {
		this.clearViewAs();
	}
	// #endregion

	// #region Private Methods
	private readStoredUser(): User | null {
		try {
			const raw = localStorage.getItem(this.storageKey);
			return raw ? (JSON.parse(raw) as User) : null;
		} catch {
			return null;
		}
	}

	private readStoredViewAs(): { level: AccessLevel; regionId?: string; schoolId?: string } | null {
		try {
			const raw = localStorage.getItem(this.viewAsKey);
			return raw ? (JSON.parse(raw) as { level: AccessLevel; regionId?: string; schoolId?: string }) : null;
		} catch {
			return null;
		}
	}

	private setViewAs(v: { level: AccessLevel; regionId?: string; schoolId?: string }): void {
		localStorage.setItem(this.viewAsKey, JSON.stringify(v));
		this.viewAsSignal.set(v);
	}

	private clearViewAs(): void {
		localStorage.removeItem(this.viewAsKey);
		this.viewAsSignal.set(null);
	}
	// #endregion
}

