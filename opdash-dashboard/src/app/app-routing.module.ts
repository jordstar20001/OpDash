import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

// Let's import the components that will be used for the routes.
import { LoginComponent } from './login/login.component';

const routes: Routes = [
  { path: 'login', component: LoginComponent }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
