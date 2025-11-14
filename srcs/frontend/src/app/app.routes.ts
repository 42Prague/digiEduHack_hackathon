import { Routes } from '@angular/router';
import { LoginPageComponent } from './pages/login/login-page.component';
import { RegionListComponent } from './pages/regions/region-list.component';
import { RegionDetailComponent } from './pages/regions/region-detail.component';
import { RegionalOverviewComponent } from './pages/regions/regional-overview.component';
import { RegionalUploadComponent } from './pages/regions/regional-upload.component';
import { SchoolListComponent } from './pages/schools/school-list.component';
import { SchoolDetailComponent } from './pages/schools/school-detail.component';
import { SchoolOverviewComponent } from './pages/schools/school-overview.component';
import { SchoolUploadComponent } from './pages/schools/school-upload.component';
import { UserListComponent } from './pages/users/user-list.component';
import { UserDetailComponent } from './pages/users/user-detail.component';
import { AuthGuard } from './core/auth.guard';
import { RegionCreateComponent } from './pages/regions/region-create.component';
import { RegionEditComponent } from './pages/regions/region-edit.component';
import { SchoolCreateComponent } from './pages/schools/school-create.component';
import { LandingComponent } from './core/landing.component';
import { GlobalOverviewComponent } from './pages/overview/global-overview.component';

export const APP_ROUTES: Routes = [
	{ path: '', pathMatch: 'full', component: LandingComponent, canActivate: [AuthGuard] },
	{ path: 'login', component: LoginPageComponent },
	{ path: 'overview/global', component: GlobalOverviewComponent, canActivate: [AuthGuard] },
	{ path: 'regions', component: RegionListComponent, canActivate: [AuthGuard] },
	{ path: 'regions/new', component: RegionCreateComponent, canActivate: [AuthGuard] },
	{ path: 'regions/:id/edit', component: RegionEditComponent, canActivate: [AuthGuard] },
	{ path: 'regions/:id', component: RegionDetailComponent, canActivate: [AuthGuard] },
	{ path: 'overview/region', component: RegionalOverviewComponent, canActivate: [AuthGuard] },
	{ path: 'upload/region', component: RegionalUploadComponent, canActivate: [AuthGuard] },
	{ path: 'schools', component: SchoolListComponent, canActivate: [AuthGuard] },
	{ path: 'schools/new', component: SchoolCreateComponent, canActivate: [AuthGuard] },
	{ path: 'schools/:id', component: SchoolDetailComponent, canActivate: [AuthGuard] },
	{ path: 'overview/school', component: SchoolOverviewComponent, canActivate: [AuthGuard] },
	{ path: 'upload/school', component: SchoolUploadComponent, canActivate: [AuthGuard] },
	{ path: 'users', component: UserListComponent, canActivate: [AuthGuard], data: { roles: ['Global'] } },
	{ path: 'users/:id', component: UserDetailComponent, canActivate: [AuthGuard], data: { roles: ['Global'] } },
	{ path: '**', redirectTo: 'login' }
];

