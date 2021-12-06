import { Component, OnInit } from '@angular/core';

import { FormControl } from '@angular/forms';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent implements OnInit {

  usernameFormControl = new FormControl("");
  passwordFormControl = new FormControl("");
  constructor() { }

  ngOnInit(): void {
  }

}
