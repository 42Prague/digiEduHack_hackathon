import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { map, Observable, of } from 'rxjs';
import { User } from '../models/user';
import { AccessLevel } from '../models/access-level';

@Injectable({ providedIn: 'root' })
export class UserService {
	// #region Private Properties
	private readonly apiBase: string = '/api/users';
	// #endregion

	// #region Public Methods
	public constructor(private readonly http: HttpClient) {}
	// #endregion

	// #region Public Methods
	public list(): Observable<User[]> {
		return this.http.get<unknown[]>(this.apiBase).pipe(
			map((items: unknown[]) => items.map((i: unknown) => this.mapApiUser(i)))
		);
	}

	public getById(id: string): Observable<User | undefined> {
		return this.http.get<unknown>(`${this.apiBase}/${encodeURIComponent(id)}`).pipe(
			map((i: unknown) => this.mapApiUser(i))
		);
	}

	public update(id: string, changes: Partial<User>): Observable<User | undefined> {
		// Update not supported by backend yet
		return of(undefined);
	}
	// #endregion

	// #region Private Methods
	private mapApiUser(raw: unknown): User {
		const o = raw as Record<string, unknown>;
		return {
			id: String(o['id'] ?? ''),
			name: String(o['name'] ?? ''),
			surname: String(o['surname'] ?? ''),
			email: String(o['email'] ?? ''),
			accessLevel: this.mapAccessLevel(String(o['access_level'] ?? ''))
		};
	}

	private mapAccessLevel(apiValue: string): AccessLevel {
		switch (apiValue) {
			case 'GLOBAL_ADMIN':
				return AccessLevel.Global;
			case 'REGION_ADMIN':
				return AccessLevel.Region;
			case 'SCHOOL_ADMIN':
				return AccessLevel.School;
			default:
				return AccessLevel.School;
		}
	}
	// #endregion
}

