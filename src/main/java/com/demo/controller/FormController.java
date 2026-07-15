package com.demo.controller;

import com.demo.model.UserSubmission;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;

@Controller
public class FormController {

    @GetMapping("/")
    public String showForm(Model model) {
        // Pass an empty object to the view to bind the form data
        model.addAttribute("submission", new UserSubmission());
        return "form";
    }

    @PostMapping("/submit")
    public String submitForm(UserSubmission submission, Model model) {
        // Receive the submitted form data and pass it to the result view
        model.addAttribute("submission", submission);
        return "result";
    }
}
