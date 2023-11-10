window.onload = codeAddress;
function codeAddress(){
    document.getElementsByClassName("loading2")[0].style.visibility="hidden";
    document.getElementById("row_branch").style.display="none";
    document.getElementById("loading").style.display="none";
    coll = document.getElementsByClassName("collapsible");
    coll[0].addEventListener("click", function(){
        this.classList.toggle("active");
        var content = this.nextElementSibling;
        if(content.style.display==="block"){
            content.style.display="none";
        }else{
            content.style.display="block";
        }
    });
}

function checkValue(){
    oFormObject = document.forms['v_form'];
    oFormMaxDepth = oFormObject.elements["max_depth"];
    if (oFormMaxDepth.value == ""){
        oFormMaxDepth.value = 10000;
    }
    oFormMaxThread = oFormObject.elements["max_thread"];
    if (oFormMaxThread.value == ""){
        oFormMaxThread.value = 15;
    }
    oFormGitBranch = oFormObject.elements["git_branch"];
    if (oFormGitBranch.value == ""){
        oFormGitBranch.value = 'master';
    }
}

function testUrl(){
    oFormObject = document.forms['v_form'];
    if(oFormObject.elements["target_url"].value.match(/\bgithub\b/g)){
        document.getElementById("row_branch").style.display="";
    }else{
        document.getElementById("row_branch").style.display="none";
    }
}

function validate(form){
    document.getElementsByClassName("loading2")[0].style.visibility="visible";
    if (form.elements["target_url"].value== ""){
        document.getElementById("message").innerHTML="You need to fill the required fields.";
        return false;
    }
    checkValue()
    document.getElementById("message").innerHTML="Broken Link checking is in progress.";
    document.getElementById("loading").style.display="inline";
    form.elements["submit_form"].style.display="none";
    return true;
}
